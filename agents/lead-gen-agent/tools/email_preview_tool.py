"""Build personalised email draft previews without sending — used for human-in-the-loop review."""
import logging

logger = logging.getLogger(__name__)


def build_email_previews(
    leads: list[dict],
    subject: str,
    message_template: str,
    from_name: str = "Sales Team",
) -> list[dict]:
    """
    Build personalised email previews from leads + templates.

    Returns a list of draft dicts that can be reviewed/edited by the user
    before being passed to send_from_drafts().

    Each draft: {lead_id, to_email, to_name, subject, body, from_name}
    """
    drafts = []
    for lead in leads:
        email = lead.get("email") or lead.get("email_address")
        if not email:
            continue

        full_name: str = lead.get("full_name") or lead.get("name") or ""
        name_parts = full_name.strip().split(" ", 1)
        first_name = name_parts[0] if name_parts else "there"
        last_name = name_parts[1] if len(name_parts) > 1 else ""
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
            personalized_subject = subject.format(**fmt)
            personalized_body = message_template.format(**fmt)
        except KeyError as exc:
            logger.warning("Template placeholder %s missing for lead %s — using raw template", exc, email)
            personalized_subject = subject
            personalized_body = message_template

        drafts.append({
            "lead_id": lead.get("id", email),
            "to_email": email,
            "to_name": full_name,
            "subject": personalized_subject,
            "body": personalized_body,
            "from_name": from_name,
        })

    logger.info("build_email_previews: built %d draft(s) from %d leads", len(drafts), len(leads))
    return drafts
