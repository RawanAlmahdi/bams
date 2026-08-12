from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.models.user import User


async def get_pending_users(
    db: AsyncSession,
) -> list[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.account_status == "PENDING")
        .order_by(User.created_at)
    )

    return list(result.scalars().all())


async def get_user_by_id(
    db: AsyncSession,
    user_id: int,
) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .execution_options(populate_existing=True)
        .where(User.id == user_id)
    )

    return result.scalar_one_or_none()


async def approve_user(
    db: AsyncSession,
    user_id: int,
    role_id: int,
) -> User:
    user = await get_user_by_id(db, user_id)

    if user is None:
        raise ValueError("User not found.")

    if user.account_status != "PENDING":
        raise ValueError("User is not pending approval.")

    result = await db.execute(
        select(Role).where(Role.id == role_id)
    )

    role = result.scalar_one_or_none()

    if role is None:
        raise ValueError("Role not found.")

    if role.name == "Pending User":
        raise ValueError(
            "A user cannot be approved with the Pending User role."
        )

    user.role_id = role.id
    user.account_status = "ACTIVE"
    user.is_active = True

    await db.commit()

    updated_user = await get_user_by_id(
        db=db,
        user_id=user.id,
    )

    if updated_user is None:
        raise RuntimeError(
            "User could not be retrieved after approval."
        )

    return updated_user


async def reject_user(
    db: AsyncSession,
    user_id: int,
) -> User:
    user = await get_user_by_id(db, user_id)

    if user is None:
        raise ValueError("User not found.")

    if user.account_status != "PENDING":
        raise ValueError("User is not pending approval.")

    user.account_status = "REJECTED"
    user.is_active = False

    await db.commit()

    updated_user = await get_user_by_id(
        db=db,
        user_id=user.id,
    )

    if updated_user is None:
        raise RuntimeError(
            "User could not be retrieved after rejection."
        )

    return updated_user