import random
import hashlib
import logging
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)

# ===== OTP CONFIG =====
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
RESEND_COOLDOWN_SECONDS = 30
DAILY_RESEND_LIMIT = 10

from threading import Thread

def send_otp_email_async(obj, email, name, purpose="verify"):
    def task():
        try:
            send_otp_email(obj, email, name, purpose)
        except Exception as e:
            import logging
            logging.error(f"Failed to send OTP email to {email}: {e}")
    Thread(target=task).start()


def generate_otp() -> str:
    """Generate a random numeric OTP."""
    return f"{random.randint(0, 10**OTP_LENGTH - 1):0{OTP_LENGTH}d}"

def hash_otp(otp: str) -> str:
    """Hash OTP with SHA-256 (never store raw OTP)."""
    return hashlib.sha256(otp.encode()).hexdigest()

def send_otp_email(obj, email: str, name: str, purpose: str = "verify"):
    """
    Works for both User.profile and PendingUser, as long as fields exist.
    - obj must have: otp_hash, otp_created_at, last_otp_sent_at, otp_resend_count, otp_attempts
    - email is recipient's email
    - name is recipient's name
    """
    now = timezone.now()

    # === Cooldown check ===
    if obj.last_otp_sent_at and (now - obj.last_otp_sent_at).total_seconds() < RESEND_COOLDOWN_SECONDS:
        return False, "OTP recently sent. Please wait before requesting again."

    # === Daily resend limit ===
    if obj.otp_resend_count >= DAILY_RESEND_LIMIT:
        if obj.last_otp_sent_at and obj.last_otp_sent_at.date() < now.date():
            obj.otp_resend_count = 0
        else:
            return False, "Daily OTP limit reached. Try again tomorrow."

    # === Generate new OTP ===
    raw_otp = generate_otp()
    obj.otp_hash = hash_otp(raw_otp)
    obj.otp_created_at = now
    obj.last_otp_sent_at = now
    obj.otp_resend_count += 1
    obj.otp_attempts = 0
    obj.save()

    # === Email content ===
    subject = f"JobLane - Your OTP for {purpose.capitalize()}"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    text_content = f"""
Hello {name},

Your OTP for JobLane ({purpose}) is: {raw_otp}
⚠️ It will expire in {OTP_EXPIRY_MINUTES} minutes.

If you did not request this, please ignore this email.
    """.strip()

    html_content = f"""
    <html>
  <body style="margin:0; padding:0; background-color:#f9fafb; font-family: Arial, sans-serif; color:#333;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
      <tr>
        <td align="center" style="padding:20px 0;">
          <!-- Container -->
          <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="max-width:600px; background:#ffffff; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.05); overflow:hidden;">
            
            <!-- Header -->
            <tr>
              <td align="center" style="background:#2563eb; padding:20px;">
                <!-- If you have a logo image, replace JobLane text with <img src="LOGO_URL" width="120" alt="JobLane" /> -->
                <h1 style="margin:0; font-size:24px; color:#ffffff; font-weight:bold;">JobLane</h1>
              </td>
            </tr>
            
            <!-- Body -->
            <tr>
              <td style="padding:30px;">
                <h2 style="margin-top:0; font-size:20px; font-weight:400;">
  Hello <span style="color:#2563eb; font-weight:600;">{name}</span>,
</h2>

                <p style="font-size:16px; line-height:1.6;">Your OTP for <strong>JobLane</strong> ({purpose}) is:</p>
                
                <!-- OTP Box -->
                <div style="text-align:center; margin:30px 0;">
                  <div style="display:inline-block; font-size:32px; font-weight:bold; color:#2563eb; letter-spacing:6px; background:#f1f5f9; padding:15px 30px; border-radius:8px; border:2px dashed #2563eb;">
                    {raw_otp}
                  </div>
                </div>
                
                <p style="font-size:14px; color:#555; margin:0;">⚠️ This OTP will expire in <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.</p>
                <p style="font-size:14px; color:#555; margin:5px 0 20px;">If you didn’t request this, you can safely ignore this email.</p>
              </td>
            </tr>
            
            <!-- Footer -->
            <tr>
              <td style="background:#f3f4f6; text-align:center; padding:15px; font-size:12px; color:#888;">
                This is an automated message from <strong>JobLane</strong>. Please do not reply.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>

    """


    try:
        msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
    except Exception as e:
        logger.error("Failed to send OTP email to %s: %s", email, str(e))
        return False, "Failed to send OTP. Please try again."

    return True, "OTP sent successfully."
