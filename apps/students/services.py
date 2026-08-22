import csv
import io

from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.batches.models import Batch
from apps.tenants.models import Tenant

from .models import Student

ROLL_PREFIX = "STU"
REQUIRED_CSV_COLUMNS = {"username", "first_name", "last_name"}


def generate_roll_number(tenant):
    """Next unique STU-0001-style roll number for this tenant (FR-2.3).

    Postgres won't allow `SELECT ... FOR UPDATE` together with an aggregate
    (`.count()`), so the lock target is the Tenant row itself rather than
    the Student rows being counted — this serializes concurrent roll-number
    generation for the same tenant without blocking other tenants.
    """
    with transaction.atomic():
        Tenant.objects.select_for_update().get(pk=tenant.pk)
        seq = Student.all_objects.filter(tenant=tenant).count() + 1
        roll_number = f"{ROLL_PREFIX}-{seq:04d}"
        while Student.all_objects.filter(tenant=tenant, roll_number=roll_number).exists():
            seq += 1
            roll_number = f"{ROLL_PREFIX}-{seq:04d}"
        return roll_number


def bulk_import_students(tenant, csv_file):
    """Create one User(role=student) + Student per CSV row (FR-2.4).

    Expected columns: username, first_name, last_name, email (optional),
    batch (optional — batch name, must already exist), roll_number
    (optional — auto-generated if blank), guardian_name, guardian_phone.

    Each row is its own transaction so one bad row (typo, unknown batch)
    is reported and skipped instead of rolling back the whole file.
    """
    decoded = io.StringIO(csv_file.read().decode("utf-8-sig"))
    reader = csv.DictReader(decoded)

    missing = REQUIRED_CSV_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(sorted(missing))}")

    created = 0
    errors = []

    for row_number, row in enumerate(reader, start=2):  # header is row 1
        username = (row.get("username") or "").strip()
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()

        if not username or not first_name:
            errors.append({"row": row_number, "error": "username and first_name are required"})
            continue

        batch_name = (row.get("batch") or "").strip()
        try:
            with transaction.atomic():
                batch = None
                if batch_name:
                    batch = Batch.all_objects.get(tenant=tenant, name=batch_name)

                user = User.all_objects.create_user(
                    username=username,
                    email=(row.get("email") or "").strip(),
                    first_name=first_name,
                    last_name=last_name,
                    tenant=tenant,
                    role=User.Role.STUDENT,
                )
                user.set_unusable_password()  # student logs in only after an explicit invite/reset
                user.save(update_fields=["password"])

                roll_number = (row.get("roll_number") or "").strip() or generate_roll_number(tenant)
                Student.all_objects.create(
                    tenant=tenant,
                    user=user,
                    batch=batch,
                    roll_number=roll_number,
                    guardian_name=(row.get("guardian_name") or "").strip(),
                    guardian_phone=(row.get("guardian_phone") or "").strip(),
                )
                created += 1
        except Batch.DoesNotExist:
            errors.append({"row": row_number, "error": f"batch '{batch_name}' not found"})
        except IntegrityError as exc:
            errors.append({"row": row_number, "error": str(exc)})

    return {"created": created, "errors": errors}
