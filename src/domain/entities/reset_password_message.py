from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field


class ResetPasswordMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    email: EmailStr
    subject: str
    body: str
    published_at: datetime
    sent_at: datetime | None = None
