import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def generate_receipt_pdf(payment) -> bytes:
    """Renders a one-page payment receipt as PDF bytes — FR-4.3.
    "Rs." instead of the rupee sign: reportlab's base14 fonts don't carry
    the glyph, so a Unicode font would need to be embedded just for this.
    """
    buffer = io.BytesIO()
    doc = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    doc.setFont("Helvetica-Bold", 16)
    doc.drawString(20 * mm, height - 25 * mm, payment.tenant.name)

    doc.setFont("Helvetica-Bold", 13)
    doc.drawString(20 * mm, height - 40 * mm, "Payment Receipt")

    doc.setFont("Helvetica", 10)
    lines = [
        f"Receipt No: RCPT-{payment.id:06d}",
        f"Date: {payment.paid_at.strftime('%d %b %Y, %I:%M %p') if payment.paid_at else '-'}",
        "",
        f"Student: {payment.student.user.get_full_name() or payment.student.user.username}",
        f"Roll No: {payment.student.roll_number}",
        f"Fee: {payment.fee_structure.name} ({payment.fee_structure.batch.name})",
        f"Amount Paid: Rs. {payment.amount_paid}",
        f"Payment ID: {payment.razorpay_payment_id or '-'}",
        f"Status: {payment.get_status_display()}",
    ]
    y = height - 55 * mm
    for line in lines:
        doc.drawString(20 * mm, y, line)
        y -= 7 * mm

    doc.showPage()
    doc.save()
    return buffer.getvalue()
