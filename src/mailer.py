"""Sends the daily report by email via Gmail SMTP, using an App Password
loaded from data/.env (never from chat, never committed — see .gitignore).

Gmail App Passwords require 2-Step Verification to be enabled on the
sending account, and the password must belong to GMAIL_SENDER specifically
(Gmail auths the SMTP login as that account, not the recipient).
"""
from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from pathlib import Path

from env_loader import load_env

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def send_report_email(report_path: Path, env_path: Path, subject: str | None = None) -> tuple[bool, str]:
    env = load_env(env_path)
    app_password = env.get("GMAIL_APP_PASSWORD", "")
    sender = env.get("GMAIL_SENDER", "")
    recipient = env.get("GMAIL_RECIPIENT", "")

    if not app_password or app_password.startswith("paste-"):
        return False, (
            f"No app password configured. Copy {env_path.parent / '.env.example'} to "
            f"{env_path} and fill in GMAIL_APP_PASSWORD."
        )
    if not sender or not recipient:
        return False, f"GMAIL_SENDER/GMAIL_RECIPIENT missing in {env_path}."

    body = report_path.read_text(encoding="utf-8")
    subject = subject or f"Remote job matches — {report_path.stem}"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.login(sender, app_password)
            server.sendmail(sender, [recipient], msg.as_string())
    except Exception as exc:  # noqa: BLE001
        return False, f"Send failed: {exc}"
    return True, f"Sent to {recipient}"


def send_status_email(env_path: Path, subject: str, body: str) -> tuple[bool, str]:
    """For error/status notifications that aren't tied to a report file."""
    env = load_env(env_path)
    app_password = env.get("GMAIL_APP_PASSWORD", "")
    sender = env.get("GMAIL_SENDER", "")
    recipient = env.get("GMAIL_RECIPIENT", "")
    if not app_password or app_password.startswith("paste-") or not sender or not recipient:
        return False, "Email not configured (see data/.env.example)."

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.login(sender, app_password)
            server.sendmail(sender, [recipient], msg.as_string())
    except Exception as exc:  # noqa: BLE001
        return False, f"Send failed: {exc}"
    return True, f"Sent to {recipient}"
