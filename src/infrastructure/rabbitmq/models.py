from datetime import datetime

from pydantic import BaseModel, EmailStr


class ResetPayload(BaseModel):
    recipient_email: EmailStr
    user_id: str
    reset_link: str


class IncomingEvent(BaseModel):
    event_type: str
    payload: ResetPayload
    occurred_at: datetime
