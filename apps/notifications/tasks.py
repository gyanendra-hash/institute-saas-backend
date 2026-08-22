from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification(self, notification_id):
    from apps.notifications.models import Notification
    notification = Notification.all_objects.select_related("user", "tenant").get(id=notification_id)
    try:
        if notification.channel == Notification.Channel.EMAIL:
            send_mail(
                notification.subject,
                notification.message,
                settings.DEFAULT_FROM_EMAIL,
                [notification.user.email],
            )
        # SMS / WhatsApp providers plugged in here (Twilio / MSG91 / Gupshup etc.)

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
    callback API returns immediately."""
    from apps.fees.models import Payment
    payment = Payment.all_objects.select_related("student__user", "tenant").get(id=payment_id)
    # PDF generation (weasyprint/reportlab) would happen here
    send_mail(
        subject="Payment Receipt",
        message=f"Payment of ₹{payment.amount_paid} received. Thank you.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[payment.student.user.email],
    )


@shared_task
def send_fee_due_reminders():
    """Scheduled via Celery Beat — runs daily, reminds students of upcoming dues."""
    from apps.fees.models import FeeStructure, Payment
    from datetime import timedelta

    upcoming = timezone.now().date() + timedelta(days=3)
    due_structures = FeeStructure.all_objects.filter(due_date=upcoming)
    for fs in due_structures:
        students = fs.batch.students.filter(is_active=True)
        for student in students:
            already_paid = Payment.all_objects.filter(
                fee_structure=fs, student=student, status=Payment.PaymentStatus.SUCCESS
            ).exists()
            if not already_paid:
                send_mail(
                    subject="Fee Due Reminder",
                    message=f"Your fee of ₹{fs.amount} for {fs.name} is due on {fs.due_date}.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[student.user.email],
                )
