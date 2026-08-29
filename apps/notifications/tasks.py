from celery import shared_task
from django.utils import timezone
from django.core.mail import EmailMessage, send_mail
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification(self, notification_id):
    """FR-6.1/6.2 — dispatches one Notification over its channel,
    asynchronously so nothing in the request/response cycle waits on it.
    FR-6.3: status is always persisted (queued -> sent/failed), whichever
    channel is used."""
    from apps.notifications.models import Notification
    from apps.notifications.services import send_sms, send_whatsapp

    notification = Notification.all_objects.select_related("user", "tenant").get(id=notification_id)
    try:
        if notification.channel == Notification.Channel.EMAIL:
            send_mail(
                notification.subject,
                notification.message,
                settings.DEFAULT_FROM_EMAIL,
                [notification.user.email],
            )
        elif notification.channel == Notification.Channel.SMS:
            send_sms(notification.user.phone, notification.message)
        elif notification.channel == Notification.Channel.WHATSAPP:
            send_whatsapp(notification.user.phone, notification.message)

        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at"])
    except Exception as exc:
        notification.status = Notification.Status.FAILED
        notification.save(update_fields=["status"])
        raise self.retry(exc=exc)


@shared_task
def send_payment_receipt(payment_id):
    """Generates the receipt PDF and emails it — kept async so the payment
    callback API returns immediately. FR-4.3."""
    from apps.fees.models import Payment
    from apps.fees.services.receipts import generate_receipt_pdf

    payment = Payment.all_objects.select_related(
        "student__user", "fee_structure__batch", "tenant"
    ).get(id=payment_id)
    pdf_bytes = generate_receipt_pdf(payment)

    email = EmailMessage(
        subject="Payment Receipt",
        body=f"Payment of Rs. {payment.amount_paid} received. Receipt attached.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[payment.student.user.email],
    )
    email.attach(f"receipt_{payment.id}.pdf", pdf_bytes, "application/pdf")
    email.send()


LOW_ATTENDANCE_THRESHOLD = 75  # percent
LOW_ATTENDANCE_LOOKBACK_DAYS = 30
LOW_ATTENDANCE_MIN_RECORDS = 5  # skip students with too little data to judge yet


@shared_task
def check_low_attendance():
    """Scheduled via Celery Beat — flags students whose attendance % over
    the trailing LOW_ATTENDANCE_LOOKBACK_DAYS is below the threshold and
    queues a notification (FR-3.4). Beat's daily schedule naturally caps
    this to one alert per student per day."""
    from datetime import timedelta
    from django.db.models import Count, Q
    from apps.attendance.models import Attendance
    from apps.students.models import Student
    from apps.notifications.models import Notification

    since = timezone.now().date() - timedelta(days=LOW_ATTENDANCE_LOOKBACK_DAYS)
    summary = (
        Attendance.all_objects.filter(date__gte=since, student__is_active=True)
        .values("student_id")
        .annotate(
            total=Count("id"),
            present=Count("id", filter=Q(status=Attendance.Status.PRESENT)),
        )
    )

    for row in summary:
        if row["total"] < LOW_ATTENDANCE_MIN_RECORDS:
            continue
        percentage = row["present"] / row["total"] * 100
        if percentage >= LOW_ATTENDANCE_THRESHOLD:
            continue

        student = Student.all_objects.select_related("user", "tenant").get(id=row["student_id"])
        notification = Notification.all_objects.create(
            tenant=student.tenant,
            user=student.user,
            channel=Notification.Channel.EMAIL,
            subject="Low Attendance Alert",
            message=(
                f"Your attendance over the last {LOW_ATTENDANCE_LOOKBACK_DAYS} days is "
                f"{percentage:.1f}%, below the required {LOW_ATTENDANCE_THRESHOLD}%."
            ),
        )
        send_notification.delay(notification.id)


@shared_task
def send_fee_due_reminders():
    """Scheduled via Celery Beat — runs daily, reminds students of upcoming
    dues (FR-4.4). Queues a Notification (like check_low_attendance) rather
    than calling send_mail directly, so reminders show up in delivery-status
    history too (FR-6.3) — the M4 version of this task sent mail inline and
    left no record."""
    from apps.fees.models import FeeStructure, Payment
    from apps.notifications.models import Notification
    from datetime import timedelta

    upcoming = timezone.now().date() + timedelta(days=3)
    due_structures = FeeStructure.all_objects.filter(due_date=upcoming)
    for fs in due_structures:
        students = fs.batch.students.filter(is_active=True)
        for student in students:
            already_paid = Payment.all_objects.filter(
                fee_structure=fs, student=student, status=Payment.PaymentStatus.SUCCESS
            ).exists()
            if already_paid:
                continue

            notification = Notification.all_objects.create(
                tenant=student.tenant,
                user=student.user,
                channel=Notification.Channel.EMAIL,
                subject="Fee Due Reminder",
                message=f"Your fee of Rs. {fs.amount} for {fs.name} is due on {fs.due_date}.",
            )
            send_notification.delay(notification.id)
