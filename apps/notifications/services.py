"""SMS/WhatsApp senders (FR-6.1). Both are Twilio-backed when
TWILIO_ACCOUNT_SID/AUTH_TOKEN are configured; otherwise they log-and-succeed
instead of raising, the same trade-off dev.py's console EMAIL_BACKEND makes
-- so notifications can be exercised end-to-end (including delivery-status
logging, FR-6.3) without a real Twilio account."""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def _twilio_configured():
    return bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)


def send_sms(phone_number, message):
    """Returns True once handed off (to Twilio, or to the log fallback)."""
    if not _twilio_configured():
        logger.info("[SMS not configured, logging only] to=%s: %s", phone_number, message)
        return True

    from twilio.rest import Client

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(body=message, from_=settings.TWILIO_FROM_NUMBER, to=phone_number)
    return True


def send_whatsapp(phone_number, message):
    """Returns True once handed off (to Twilio's WhatsApp API, or the log
    fallback)."""
    if not _twilio_configured():
        logger.info("[WhatsApp not configured, logging only] to=%s: %s", phone_number, message)
        return True

    from twilio.rest import Client

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
        to=f"whatsapp:{phone_number}",
    )
    return True
