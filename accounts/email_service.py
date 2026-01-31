import logging
import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def send_email_console(email, subject, text_content, html_content):
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        to=[email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    return True


def send_email_brevo(email, name, subject, text_content, html_content):
    payload = {
        "sender": {
            "name": "Joblane",
            "email": settings.DEFAULT_FROM_EMAIL,
        },
        "to": [{"email": email, "name": name}],
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text_content,
    }

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        json=payload,
        headers=headers,
        timeout=5,
    )

    if response.status_code >= 400:
        logger.error(f"Brevo email failed: {response.text}")
        return False

    return True


def send_email(
    *,
    email: str,
    name: str,
    subject: str,
    text_content: str,
    html_content: str,
):
    provider = settings.EMAIL_PROVIDER

    if provider == "console":
        return send_email_console(
            email, subject, text_content, html_content
        )

    if provider == "brevo":
        return send_email_brevo(
            email, name, subject, text_content, html_content
        )

    raise RuntimeError(f"Unknown EMAIL_PROVIDER: {provider}")
