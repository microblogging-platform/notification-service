import logging

import aioboto3
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import EmailStr

from domain.exceptions import EmailSendingError
from domain.interfaces.services.email_sender import IEmailSender

logger = logging.getLogger(__name__)

TEMPLATE_DIR = "src/templates"

class SesEmailSender(IEmailSender):

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
        sender: str,
    ) -> None:
        self._sender = sender
        self._session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
        )
        self._jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=select_autoescape(["html"]),
        )

    async def send_email(self, to: EmailStr, subject: str, body: str) -> None:
        template = self._jinja_env.get_template("reset_password.html")
        html_body = template.render(username=to, reset_link=body)

        try:
            async with self._session.client("ses") as ses:
                await ses.send_email(
                    Source=self._sender,
                    Destination={"ToAddresses": [to]},
                    Message={
                        "Subject": {"Data": subject, "Charset": "UTF-8"},
                        "Body": {
                            "Html": {"Data": html_body, "Charset": "UTF-8"},
                        },
                    },
                )
            logger.info("Email sent via SES to %s.", to)
        except Exception as exc:
            logger.exception("Failed to send email via SES to %s.", to)
            raise EmailSendingError(f"SES send failed for {to}") from exc
