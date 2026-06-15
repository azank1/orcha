"""
Email outreach tool — sends personalised cold-outreach emails to qualified leads.
Supports Resend (preferred) and SendGrid. Provider is auto-detected from env keys.
Falls back gracefully if no provider key or FROM_EMAIL is configured.
"""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _get_resend_key() -> str | None:
    from core.context import get_key
    return get_key("RESEND_API_KEY") or os.getenv("RESEND_API_KEY")


def _get_sendgrid_key() -> str | None:
    from core.context import get_key
    return get_key("SENDGRID_API_KEY") or os.getenv("SENDGRID_API_KEY")


def _get_gmail_password() -> str | None:
    from core.context import get_key
    return get_key("GMAIL_APP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")


def _get_from_email() -> str | None:
    from core.context import get_key
    return get_key("FROM_EMAIL") or os.getenv("FROM_EMAIL")


async def _send_via_gmail_smtp(drafts: list[dict], from_email: str, app_password: str) -> dict:
    """Send pre-built drafts via Gmail SMTP using an App Password."""
    import smtplib
    import asyncio
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    results = []
    sent = failed = skipped = 0

    def _send_sync():
        nonlocal sent, failed, skipped
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(from_email, app_password)
            for draft in drafts:
                to_email = draft.get("to_email")
                if not to_email:
                    skipped += 1
                    results.append({"email": None, "status": "skipped", "reason": "no email address"})
                    continue
                try:
                    msg = MIMEMultipart()
                    msg["From"] = f"{draft.get('from_name', 'Sales Team')} <{from_email}>"
                    msg["To"] = to_email
                    msg["Subject"] = draft.get("subject", "")
                    msg.attach(MIMEText(draft.get("body", ""), "plain"))
                    smtp.sendmail(from_email, to_email, msg.as_string())
                    sent += 1
                    results.append({"email": to_email, "status": "sent", "reason": "Gmail SMTP 250"})
                    logger.info("Gmail SMTP: sent to %s", to_email)
                except Exception as exc:
                    failed += 1
                    results.append({"email": to_email, "status": "failed", "reason": str(exc)})
                    logger.error("Gmail SMTP: failed to send to %s: %s", to_email, exc)

    await asyncio.get_event_loop().run_in_executor(None, _send_sync)
    logger.info("_send_via_gmail_smtp: sent=%d failed=%d skipped=%d", sent, failed, skipped)
    return {"sent": sent, "failed": failed, "skipped_no_email": skipped, "results": results}


async def _send_via_resend(drafts: list[dict], from_email: str, api_key: str) -> dict:
    """Send pre-built drafts via Resend API."""
    import httpx

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    results = []
    sent = failed = skipped = 0

    async with httpx.AsyncClient(timeout=15) as client:
        for draft in drafts:
            to_email = draft.get("to_email")
            if not to_email:
                skipped += 1
                results.append({"email": None, "status": "skipped", "reason": "no email address"})
                continue

            payload = {
                "from": f"{draft.get('from_name', 'Sales Team')} <{from_email}>",
                "to": [to_email],
                "subject": draft.get("subject", ""),
                "text": draft.get("body", ""),
            }

            try:
                resp = await client.post("https://api.resend.com/emails", json=payload, headers=headers)
                if resp.status_code in (200, 201):
                    sent += 1
                    results.append({"email": to_email, "status": "sent", "reason": f"HTTP {resp.status_code}"})
                    logger.info("Resend: sent to %s", to_email)
                else:
                    failed += 1
                    results.append({"email": to_email, "status": "failed", "reason": f"HTTP {resp.status_code}: {resp.text[:200]}"})
                    logger.warning("Resend: %d for %s — %s", resp.status_code, to_email, resp.text[:200])
            except Exception as exc:
                failed += 1
                results.append({"email": to_email, "status": "failed", "reason": str(exc)})
                logger.error("Resend: failed to send to %s: %s", to_email, exc)

    logger.info("_send_via_resend: sent=%d failed=%d skipped=%d", sent, failed, skipped)
    return {"sent": sent, "failed": failed, "skipped_no_email": skipped, "results": results}


async def send_outreach_emails(
    leads: list[dict[str, Any]],
    subject: str,
    message_template: str,
    from_name: str = "Sales Team",
) -> dict[str, Any]:
    """
    Send personalised outreach emails to a list of qualified leads via SendGrid.

    Args:
        leads:            List of lead dicts. Each must have at least ``email`` and
                          ``full_name`` (or ``name``). Optional: ``title``, ``company``.
        subject:          Email subject line. Supports {first_name}, {company} placeholders.
        message_template: Email body. Supports {first_name}, {last_name}, {full_name},
                          {title}, {company} placeholders.
        from_name:        Display name for the From address.

    Returns:
        {
          "sent": <int>,
          "failed": <int>,
          "skipped_no_email": <int>,
          "results": [ {"email": str, "status": "sent"|"failed"|"skipped", "reason": str} ]
        }
    """
    api_key = _get_sendgrid_key()
    from_email = _get_from_email()

    if not api_key:
        return {
            "sent": 0,
            "failed": 0,
            "skipped_no_email": 0,
            "error": "SENDGRID_API_KEY is not configured. Set it in the agent's credentials.",
            "results": [],
        }
    if not from_email:
        return {
            "sent": 0,
            "failed": 0,
            "skipped_no_email": 0,
            "error": "FROM_EMAIL is not set. Add FROM_EMAIL=you@domain.com to the agent environment.",
            "results": [],
        }

    try:
        import sendgrid as sg_module
        from sendgrid.helpers.mail import Mail, To
    except ImportError:
        return {
            "sent": 0,
            "failed": 0,
            "skipped_no_email": 0,
            "error": "sendgrid package not installed. Run: pip install sendgrid",
            "results": [],
        }

    client = sg_module.SendGridAPIClient(api_key)
    results = []
    sent = failed = skipped = 0

    for lead in leads:
        email = lead.get("email") or lead.get("email_address")
        if not email:
            skipped += 1
            results.append({"email": None, "status": "skipped", "reason": "no email address"})
            continue

        full_name: str = lead.get("full_name") or lead.get("name") or ""
        parts = full_name.strip().split(" ", 1)
        first_name = parts[0] if parts else "there"
        last_name = parts[1] if len(parts) > 1 else ""
        title = lead.get("title") or lead.get("job_title") or ""
        company = lead.get("company") or lead.get("company_name") or ""

        fmt = {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "title": title,
            "company": company,
        }

        try:
            personalised_subject = subject.format(**fmt)
            personalised_body = message_template.format(**fmt)

            message = Mail(
                from_email=(from_email, from_name),
                to_emails=To(email, full_name),
                subject=personalised_subject,
                plain_text_content=personalised_body,
            )
            response = client.send(message)
            if response.status_code in (200, 202):
                sent += 1
                results.append({"email": email, "status": "sent", "reason": f"HTTP {response.status_code}"})
                logger.info("Email sent to %s (%s)", email, full_name)
            else:
                failed += 1
                results.append({"email": email, "status": "failed", "reason": f"HTTP {response.status_code}"})
                logger.warning("SendGrid returned %d for %s", response.status_code, email)
        except Exception as exc:
            failed += 1
            results.append({"email": email, "status": "failed", "reason": str(exc)})
            logger.error("Failed to send to %s: %s", email, exc)

    logger.info("send_outreach_emails: sent=%d failed=%d skipped=%d", sent, failed, skipped)
    return {
        "sent": sent,
        "failed": failed,
        "skipped_no_email": skipped,
        "results": results,
    }


async def send_from_drafts(drafts: list[dict]) -> dict[str, Any]:
    """
    Send pre-built email drafts (personalised + approved by user).
    Auto-selects Resend → SendGrid based on which key is configured.

    Each draft: {to_email, to_name, subject, body, from_name}
    """
    from_email = _get_from_email()
    if not from_email:
        return {"sent": 0, "failed": 0, "skipped_no_email": 0,
                "error": "FROM_EMAIL is not set in the agent environment.", "results": []}

    # Gmail SMTP (no domain needed — use when GMAIL_APP_PASSWORD is set)
    gmail_password = _get_gmail_password()
    if gmail_password:
        logger.info("send_from_drafts: using Gmail SMTP provider")
        return await _send_via_gmail_smtp(drafts, from_email, gmail_password)

    # Resend
    resend_key = _get_resend_key()
    if resend_key:
        logger.info("send_from_drafts: using Resend provider")
        return await _send_via_resend(drafts, from_email, resend_key)

    # SendGrid fallback
    sg_key = _get_sendgrid_key()
    if not sg_key:
        return {"sent": 0, "failed": 0, "skipped_no_email": 0,
                "error": "No email provider configured. Set RESEND_API_KEY or SENDGRID_API_KEY.", "results": []}

    try:
        import sendgrid as sg_module
        from sendgrid.helpers.mail import Mail, To
    except ImportError:
        return {"sent": 0, "failed": 0, "skipped_no_email": 0,
                "error": "sendgrid package not installed.", "results": []}

    logger.info("send_from_drafts: using SendGrid provider")
    client = sg_module.SendGridAPIClient(sg_key)
    results = []
    sent = failed = skipped = 0

    for draft in drafts:
        to_email = draft.get("to_email")
        if not to_email:
            skipped += 1
            results.append({"email": None, "status": "skipped", "reason": "no email address"})
            continue
        try:
            message = Mail(
                from_email=(from_email, draft.get("from_name", "Sales Team")),
                to_emails=To(to_email, draft.get("to_name", "")),
                subject=draft.get("subject", ""),
                plain_text_content=draft.get("body", ""),
            )
            response = client.send(message)
            if response.status_code in (200, 202):
                sent += 1
                results.append({"email": to_email, "status": "sent", "reason": f"HTTP {response.status_code}"})
            else:
                failed += 1
                results.append({"email": to_email, "status": "failed", "reason": f"HTTP {response.status_code}"})
        except Exception as exc:
            failed += 1
            results.append({"email": to_email, "status": "failed", "reason": str(exc)})
            logger.error("SendGrid: failed to send to %s: %s", to_email, exc)

    logger.info("send_from_drafts: sent=%d failed=%d skipped=%d", sent, failed, skipped)
    return {"sent": sent, "failed": failed, "skipped_no_email": skipped, "results": results}
