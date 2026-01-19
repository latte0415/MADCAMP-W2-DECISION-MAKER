from __future__ import annotations

import os
from dataclasses import dataclass

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class MailerError(Exception):
    pass


@dataclass(slots=True)
class SendGridMailer:
    api_key: str
    from_email: str

    def send_password_reset_email(self, *, to_email: str, reset_link: str) -> None:
        subject = "DECISION MAKER 비밀번호 재설정"
        text = f"링크를 눌러 비밀번호를 재설정하세요:\n{reset_link}\n\n이 요청을 본인이 하지 않았다면, 이 이메일을 무시하셔도 됩니다."
        html = f"""
        <p>비밀번호 재설정을 요청하셨습니다.</p>
        <p>아래 링크를 눌러 비밀번호를 재설정하세요:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>요청하지 않았다면 이 이메일을 무시하세요.</p>
        """

        msg = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=text,
            html_content=html,
        )

        try:
            client = SendGridAPIClient(self.api_key)
            resp = client.send(msg)
            # Optional: treat non-2xx as error
            if resp.status_code < 200 or resp.status_code >= 300:
                raise MailerError(f"SendGrid failed with status {resp.status_code}")
        except Exception as e:
            raise MailerError("Failed to send email") from e


def build_sendgrid_mailer_from_env() -> SendGridMailer:
    api_key = os.getenv("SENDGRID_API_KEY", "").strip()
    from_email = os.getenv("SENDGRID_FROM_EMAIL", "").strip()
    if not api_key:
        raise RuntimeError("SENDGRID_API_KEY is not set")
    if not from_email:
        raise RuntimeError("SENDGRID_FROM_EMAIL is not set")
    return SendGridMailer(api_key=api_key, from_email=from_email)
