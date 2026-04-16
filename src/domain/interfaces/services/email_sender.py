from abc import ABC, abstractmethod

from pydantic import EmailStr


class IEmailSender(ABC):

    @abstractmethod
    async def send_email(self, to: EmailStr, subject: str, body: str) -> None:
        pass