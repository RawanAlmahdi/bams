from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.department_location import DepartmentLocation
from app.models.location import Location


async def get_department_locations(
    db: AsyncSession,
) -> list[DepartmentLocation]:
    result = await db.execute(
        select(DepartmentLocation)
        .order_by(DepartmentLocation.department_id)
    )

    return list(result.scalars().all())


async def get_department_location_by_id(
    db: AsyncSession,
    department_location_id: int,
) -> DepartmentLocation | None:
    result = await db.execute(
        select(DepartmentLocation).where(
            DepartmentLocation.id == department_location_id
        )
    )

    return result.scalar_one_or_none()


async def create_department_location(
    db: AsyncSession,
    department_id: int,
    location_id: int,
) -> DepartmentLocation:

    # Check department
    result = await db.execute(
        select(Department).where(
            Department.id == department_id
        )
    )

    department = result.scalar_one_or_none()

    if department is None:
        raise ValueError("Department not found.")

    if not department.is_active:
        raise ValueError("Department is inactive.")

    # Check location
    result = await db.execute(
        select(Location).where(
            Location.id == location_id
        )
    )

    location = result.scalar_one_or_none()

    if location is None:
        raise ValueError("Location not found.")

    if not location.is_active:
        raise ValueError("Location is inactive.")

    # Prevent duplicate relationship
    result = await db.execute(
        select(DepartmentLocation).where(
            DepartmentLocation.department_id == department_id,
            DepartmentLocation.location_id == location_id,
        )
    )

    existing = result.scalar_one_or_none()

    if existing is not None:
        raise ValueError(
            "Department is already assigned to this location."
        )

    department_location = DepartmentLocation(
        department_id=department_id,
        location_id=location_id,
    )

    db.add(department_location)

    await db.commit()
    await db.refresh(department_location)

    return department_location


async def delete_department_location(
    db: AsyncSession,
    department_location_id: int,
) -> None:

    department_location = await get_department_location_by_id(
        db,
        department_location_id,
    )

    if department_location is None:
        raise ValueError(
            "Department-location assignment not found."
        )

    await db.delete(department_location)
    await db.commit()