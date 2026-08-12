import asyncio

from sqlalchemy import select

from app.auth.security import hash_password
from app.config.settings import settings
from app.db.database import AsyncSessionLocal
from app.models.role import Role
from app.models.user import User


ROLES = [
    "Pending User",
    "System Administrator",
    "Biomedical Engineer",
    "Security Guard",
    "Doctor",
    "RPD Doctor",
    "Nurse",
    "Technician",
]


async def seed_roles(session):
    for role_name in ROLES:
        result = await session.execute(
            select(Role).where(Role.name == role_name)
        )

        existing_role = result.scalar_one_or_none()

        if existing_role is None:
            session.add(Role(name=role_name))

    await session.flush()


async def seed_admin(session):
    result = await session.execute(
        select(Role).where(Role.name == "System Administrator")
    )

    admin_role = result.scalar_one_or_none()

    if admin_role is None:
        raise RuntimeError("System Administrator role was not created.")

    result = await session.execute(
        select(User).where(
            User.username == settings.INITIAL_ADMIN_USERNAME
        )
    )

    existing_admin = result.scalar_one_or_none()

    if existing_admin is None:
        admin = User(
            username=settings.INITIAL_ADMIN_USERNAME,
            password_hash=hash_password(
                settings.INITIAL_ADMIN_PASSWORD
            ),
            full_name="System Administrator",
            role_id=admin_role.id,
            account_status="ACTIVE",
            is_active=True,
        )

        session.add(admin)


async def seed():
    async with AsyncSessionLocal() as session:
        await seed_roles(session)
        await seed_admin(session)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
    print("Database seeded successfully.")