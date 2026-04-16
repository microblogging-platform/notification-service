from abc import ABC, abstractmethod

from motor.core import AgnosticClientSession

from domain.entities import ResetPasswordMessage


class INotificationRepository(ABC):

    @abstractmethod
    async def save(
        self,
        message: ResetPasswordMessage,
        session: AgnosticClientSession | None = None,
    ) -> None:
        pass
