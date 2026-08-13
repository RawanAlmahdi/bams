from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    entity_type: str | None
    entity_id: int | None
    is_read: bool
    action_required: bool
    created_at: datetime