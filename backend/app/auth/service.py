#What does the authentication operation actually do?

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password, verify_password
from app.models.role import Role
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

async def register_user(
    db: AsyncSession,
    username: str,
    password: str,
    full_name: str,
    phone: str | None = None,
) -> User:
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == username)
    )

    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        raise ValueError("Username already exists")

    # Find the Pending User role
    result = await db.execute(
        select(Role).where(Role.name == "Pending User")
    )

    pending_role = result.scalar_one_or_none()

    if pending_role is None:
        raise RuntimeError("Pending User role does not exist.")

    # Create the registration request
    user = User(
        username=username,
        password_hash=hash_password(password),
        full_name=full_name,
        phone=phone,
        role_id=pending_role.id,
        account_status="PENDING",
        is_active=False,
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user