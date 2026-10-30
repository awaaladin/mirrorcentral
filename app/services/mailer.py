"""Every email Mirror sends goes through here.

Rules:
* An email problem (bad SMTP login, provider outage) can NEVER fail the request that triggered it:
  `send_email` logs and returns False instead of raising.
* Nothing is sent until the database transaction commits (see email_events.py), so a rolled-back
  payment never produces a receipt.
* All user-supplied text is HTML-escaped and subjects have newlines stripped.
* Logs name the template and a masked address, never the full recipient or a link.

Delivery is Gmail SMTP for now (a domain-based provider such as Resend later: change only the EMAIL_*
settings). With no EMAIL_HOST_PASSWORD set (local development, tests) nothing is sent and the
email is only logged.
"""
from __future__ import annotations

import logging
import os
import re
import smtplib
import ssl
from email.message import EmailMessage
from html import escape

logger = logging.getLogger(__name__)

BRAND = "Mirror"


def _mask(address: str) -> str:
    name, _, domain = (address or "").partition("@")
    return f"{name[:1]}***@{domain}"


def _setting(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def public_base_url() -> str:
    return (_setting("PUBLIC_BASE_URL") or "https://mirrorcentral.vercel.app").rstrip("/")


def render(headline: str, paragraphs: list[str], button: tuple[str, str] | None = None) -> tuple[str, str]:
    """(html, plain text) for a simple branded email. Every string is escaped here."""
    support = _setting("SUPPORT_EMAIL") or _setting("EMAIL_HOST_USER")
    body = "".join(f'<p style="margin:0 0 16px 0;">{escape(p)}</p>' for p in paragraphs)
    cta = ""
    if button:
        label, url = button
        cta = (
            f'<p style="margin:0 0 18px 0;"><a href="{escape(url, quote=True)}" style="display:inline-block;'
            f'background:#0b192c;color:#ffffff;text-decoration:none;padding:12px 20px;border-radius:10px;">{escape(label)}</a></p>'
            f'<p style="margin:0 0 8px 0;font-size:13px;color:#64748b;">If the button does not work, copy this link into your browser:</p>'
            f'<p style="margin:0;font-size:13px;word-break:break-all;">{escape(url)}</p>'
        )
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f5f7fa;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f7fa;padding:24px 12px;"><tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;">
<tr><td style="padding:0 4px 16px 4px;font-family:Arial,Helvetica,sans-serif;font-size:22px;font-weight:bold;color:#0b192c;">{BRAND}</td></tr>
<tr><td style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:28px 26px;font-family:Arial,Helvetica,sans-serif;color:#0b192c;font-size:15px;line-height:1.55;">
<h1 style="margin:0 0 12px 0;font-size:22px;line-height:1.3;">{escape(headline)}</h1>{body}{cta}</td></tr>
<tr><td style="padding:16px 8px 0 8px;font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.5;color:#64748b;text-align:center;">Questions? Write to {escape(support)}.</td></tr>
</table></td></tr></table></body></html>"""
    lines = [headline, "", *paragraphs]
    if button:
        lines += ["", f"{button[0]}: {button[1]}"]
    return html, "\n".join(lines)


def send_email(to: str, subject: str, headline: str, paragraphs: list[str], button: tuple[str, str] | None = None) -> bool:
    """Sends one email. Never raises."""
    if not to:
        return False
    try:
        password = _setting("EMAIL_HOST_PASSWORD")
        user = _setting("EMAIL_HOST_USER")
        if not password or not user:
            logger.info("Email not configured; would have sent '%s' to %s", re.sub(r"\s+", " ", subject), _mask(to))
            return False
        html, text = render(headline, paragraphs, button)
        message = EmailMessage()
        message["Subject"] = " ".join(subject.split())
        message["From"] = _setting("EMAIL_FROM") or user
        message["To"] = to
        message.set_content(text)
        message.add_alternative(html, subtype="html")

        host = _setting("EMAIL_HOST", "smtp.gmail.com")
        port = int(_setting("EMAIL_PORT", "465"))
        use_ssl = _setting("EMAIL_USE_SSL", "true").lower() in ("1", "true", "yes")
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=8, context=ssl.create_default_context()) as smtp:
                smtp.login(user, password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=8) as smtp:
                smtp.starttls(context=ssl.create_default_context())
                smtp.login(user, password)
                smtp.send_message(message)
        logger.info("Sent '%s' to %s", re.sub(r"\s+", " ", subject), _mask(to))
        return True
    except Exception:  # noqa: BLE001 - email trouble must never break the caller
        logger.exception("Could not send an email to %s", _mask(to))
        return False


def naira_from_kobo(kobo: int) -> str:
    return "₦{:,.2f}".format(int(kobo) / 100)


def send_welcome(email: str) -> bool:
    return send_email(
        email,
        "Welcome to Mirror",
        "Welcome to Mirror",
        ["Your account is ready.", "Open the app to try shades on a client, build looks, and share them."],
    )


def send_receipt(email: str, amount_kobo: int, reference: str) -> bool:
    return send_email(
        email,
        f"Your Mirror receipt: {naira_from_kobo(amount_kobo)}",
        "Payment received",
        [
            "Thank you. Here is your receipt.",
            f"Amount: {naira_from_kobo(amount_kobo)}",
            f"Reference: {reference}",
            "Keep this email as your record. Your access updates in the app straight away.",
        ],
    )


def send_password_reset(email: str, link: str) -> bool:
    return send_email(
        email,
        "Reset your Mirror password",
        "Reset your password",
        [
            "Someone asked to reset the password for this account. If that was you, choose a new one with the link below. "
            "It works once and expires in one hour.",
            "If you did not ask for this, ignore this email. Your password will not change.",
        ],
        ("Choose a new password", link),
    )
