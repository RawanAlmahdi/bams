import asyncio

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.role import Role


ROLES = [
    "System Administrator",
    "Biomedical Engineer",
    "Security Guard",
    "Doctor",
    "Nurse",
    "Technician",
]


async def seed_roles():
    async with AsyncSessionLocal() as session:
        for role_name in ROLES:
            result = await session.execute(
                select(Role).where(Role.name == role_name)
            )

            existing_role = result.scalar_one_or_none()

            if existing_role is None:
                session.add(Role(name=role_name))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_roles())
    print("Roles seeded successfully.")