import razorpay
from django.conf import settings
from django.utils import timezone
from apps.fees.models import Payment


class RazorpayService:
    def __init__(self):
        self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    def create_order(self, payment: Payment):
        """Creates a Razorpay order for the given Payment record and stores the order id."""
        order = self.client.order.create({
            "amount": int(payment.amount_paid * 100),  # paise
            "currency": "INR",
            "receipt": f"receipt_{payment.id}",
            "notes": {"tenant_id": str(payment.tenant_id), "student_id": str(payment.student_id)},
        })
        payment.razorpay_order_id = order["id"]
        payment.save(update_fields=["razorpay_order_id"])
        return order

    def verify_and_mark_paid(self, payment: Payment, razorpay_payment_id, razorpay_signature):
        """Verifies the payment signature and marks the Payment as successful.
        Called from the webhook / client-callback endpoint."""
        params = {
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }
        self.client.utility.verify_payment_signature(params)  # raises SignatureVerificationError on failure

        payment.razorpay_payment_id = razorpay_payment_id
        payment.status = Payment.PaymentStatus.SUCCESS
        payment.paid_at = timezone.now()
        payment.save(update_fields=["razorpay_payment_id", "status", "paid_at"])

        from apps.notifications.tasks import send_payment_receipt
        send_payment_receipt.delay(payment.id)  # async PDF + notification

        return payment
