from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import verify_password
from app.models.user import User


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str,
) -> User | None:
    """
    Find the user and verify their password.

    Returns the User if authentication succeeds.
    Returns None if the username or password is incorrect.
    """

    result = await db.execute(
        select(User).where(User.username == username)
    )

    user = result.scalar_one_or_none()

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user