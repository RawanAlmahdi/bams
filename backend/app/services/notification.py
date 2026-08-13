from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    action_required: bool = False,
) -> Notification:

    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        entity_type=entity_type,
        entity_id=entity_id,
        is_read=False,
        action_required=action_required,
    )

    db.add(notification)

    await db.flush()

    return notification


async def get_user_notifications(
    db: AsyncSession,
    user_id: int,
) -> list[Notification]:

    result = await db.execute(
        select(Notification)
        .where(
            Notification.user_id == user_id,
        )
        .order_by(
            Notification.created_at.desc(),
        )
    )

    return list(result.scalars().all())


async def get_unread_notifications(
    db: AsyncSession,
    user_id: int,
) -> list[Notification]:

    result = await db.execute(
        select(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .order_by(
            Notification.created_at.desc(),
        )
    )

    return list(result.scalars().all())


async def mark_notification_as_read(
    db: AsyncSession,
    notification_id: int,
    user_id: int,
) -> Notification | None:

    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )

    notification = result.scalar_one_or_none()

    if notification is None:
        return None

    notification.is_read = True

    await db.commit()
    await db.refresh(notification)

    return notification