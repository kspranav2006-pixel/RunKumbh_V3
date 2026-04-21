"""Email service for sending BIB card emails via Gmail SMTP."""
import os
import smtplib
import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formataddr

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _get_config():
    """Read Gmail credentials at call time so .env is already loaded."""
    return {
        "user": os.environ.get("GMAIL_USER", ""),
        "password": os.environ.get("GMAIL_APP_PASSWORD", ""),
        "from_name": os.environ.get("FROM_NAME", "RunKumbh 2026 Team"),
    }


def _decode_bib_card(bib_card_data_url: str) -> bytes:
    """Strip the data URL prefix and return raw PNG bytes."""
    if not bib_card_data_url:
        return b""
    if "," in bib_card_data_url:
        _, b64 = bib_card_data_url.split(",", 1)
    else:
        b64 = bib_card_data_url
    return base64.b64decode(b64)


def _build_html(user_name: str, bib_number: str, event_title: str, event_date: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;color:#111827;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f3f4f6;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
        <tr>
          <td style="background:linear-gradient(135deg,#0D7377 0%,#14AEB8 100%);padding:32px;text-align:center;color:#ffffff;">
            <h1 style="margin:0;font-size:28px;letter-spacing:1px;">RunKumbh 2026</h1>
            <p style="margin:6px 0 0;opacity:0.9;font-size:14px;">Monsoon Run 2.0 · RV Institute</p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;">
            <h2 style="margin:0 0 12px;color:#0D7377;font-size:22px;">You're In, {user_name}! 🎉</h2>
            <p style="font-size:16px;line-height:1.6;color:#374151;margin:0 0 20px;">
              Your registration for <strong>{event_title}</strong> is <strong style="color:#059669;">confirmed</strong>.
              We can't wait to see you at the start line on <strong>{event_date}</strong>.
            </p>

            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F5F5DC;border:2px dashed #0D7377;border-radius:10px;padding:20px;margin:20px 0;">
              <tr><td align="center">
                <p style="margin:0;font-size:13px;letter-spacing:2px;color:#6b7280;">YOUR BIB NUMBER</p>
                <p style="margin:6px 0 0;font-size:42px;font-weight:900;color:#0D7377;letter-spacing:3px;">{bib_number}</p>
              </td></tr>
            </table>

            <p style="font-size:15px;line-height:1.6;color:#374151;margin:0 0 12px;">
              Your personalized <strong>BIB Card</strong> is attached below. Save it on your phone or print it — you'll need to present it at the race-day check-in counter.
            </p>

            <div style="text-align:center;margin:24px 0;">
              <img src="cid:bibcard" alt="BIB Card" style="max-width:100%;border-radius:10px;border:1px solid #e5e7eb;" />
            </div>

            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FFF7ED;border-left:4px solid #FF6B35;border-radius:6px;padding:16px;margin:24px 0;">
              <tr><td>
                <p style="margin:0 0 6px;font-weight:700;color:#9A3412;">📋 Race Day Essentials</p>
                <ul style="margin:0;padding-left:20px;color:#7C2D12;font-size:14px;line-height:1.8;">
                  <li>Arrive 45 minutes before your flag-off</li>
                  <li>Carry a government photo ID + this BIB card</li>
                  <li>Wear the event T-shirt handed at registration</li>
                  <li>Stay hydrated and stretch before the run</li>
                </ul>
              </td></tr>
            </table>

            <p style="font-size:14px;color:#6b7280;margin:24px 0 0;">
              Questions? Just reply to this email and our team will get back to you.
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#0D7377;padding:20px;text-align:center;color:#ffffff;font-size:13px;">
            <p style="margin:0;">RunKumbh · Monsoon Run 2.0 · RV Institute, Bengaluru</p>
            <p style="margin:4px 0 0;opacity:0.8;">© 2026 RunKumbh. All rights reserved.</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def send_bib_email(
    to_email: str,
    user_name: str,
    bib_number: str,
    bib_card_data_url: str,
    event_title: str = "Monsoon Run 2.0",
    event_date: str = "30th May 2026",
) -> bool:
    """Send the BIB confirmation email with the BIB card image embedded and attached."""
    cfg = _get_config()
    gmail_user = cfg["user"]
    gmail_password = cfg["password"]
    from_name = cfg["from_name"]

    if not gmail_user or not gmail_password:
        logger.warning("Gmail credentials not configured; skipping email.")
        return False

    try:
        msg = MIMEMultipart("related")
        msg["Subject"] = f"🏃 You're registered! BIB {bib_number} — RunKumbh 2026"
        msg["From"] = formataddr((from_name, gmail_user))
        msg["To"] = to_email

        alt = MIMEMultipart("alternative")
        msg.attach(alt)

        text_body = (
            f"Hi {user_name},\n\n"
            f"Your registration for {event_title} is confirmed.\n"
            f"BIB Number: {bib_number}\n"
            f"Event Date: {event_date}\n\n"
            "Your BIB card is attached. Please carry it on race day along with a photo ID.\n\n"
            "— RunKumbh 2026 Team"
        )
        alt.attach(MIMEText(text_body, "plain"))
        alt.attach(MIMEText(_build_html(user_name, bib_number, event_title, event_date), "html"))

        # Embed and attach BIB card image
        img_bytes = _decode_bib_card(bib_card_data_url)
        if img_bytes:
            inline_img = MIMEImage(img_bytes, _subtype="png")
            inline_img.add_header("Content-ID", "<bibcard>")
            inline_img.add_header("Content-Disposition", "inline", filename=f"BIB_{bib_number}.png")
            msg.attach(inline_img)

            attach_img = MIMEImage(img_bytes, _subtype="png")
            attach_img.add_header("Content-Disposition", "attachment", filename=f"BIB_{bib_number}.png")
            msg.attach(attach_img)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(gmail_user, gmail_password.replace(" ", ""))
            server.sendmail(gmail_user, [to_email], msg.as_string())

        logger.info(f"BIB email sent to {to_email} (BIB {bib_number})")
        return True
    except Exception as e:
        logger.exception(f"Failed to send BIB email to {to_email}: {e}")
        return False
