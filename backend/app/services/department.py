from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department


async def get_departments(
    db: AsyncSession,
) -> list[Department]:
    result = await db.execute(
        select(Department).order_by(Department.name)
    )

    return list(result.scalars().all())


async def get_department_by_id(
    db: AsyncSession,
    department_id: int,
) -> Department | None:
    result = await db.execute(
        select(Department).where(
            Department.id == department_id
        )
    )

    return result.scalar_one_or_none()


async def create_department(
    db: AsyncSession,
    name: str,
) -> Department:

    result = await db.execute(
        select(Department).where(
            Department.name == name
        )
    )

    existing = result.scalar_one_or_none()

    if existing is not None:
        raise ValueError("Department name already exists.")

    department = Department(
        name=name,
        is_active=True,
    )

    db.add(department)

    await db.commit()
    await db.refresh(department)

    return department


async def update_department(
    db: AsyncSession,
    department_id: int,
    name: str,
) -> Department:

    department = await get_department_by_id(
        db,
        department_id,
    )

    if department is None:
        raise ValueError("Department not found.")

    result = await db.execute(
        select(Department).where(
            Department.name == name,
            Department.id != department_id,
        )
    )

    existing = result.scalar_one_or_none()

    if existing is not None:
        raise ValueError("Department name already exists.")

    department.name = name

    await db.commit()
    await db.refresh(department)

    return department


async def deactivate_department(
    db: AsyncSession,
    department_id: int,
) -> Department:

    department = await get_department_by_id(
        db,
        department_id,
    )

    if department is None:
        raise ValueError("Department not found.")

    department.is_active = False

    await db.commit()
    await db.refresh(department)

    return department