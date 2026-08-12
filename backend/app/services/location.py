from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.floor import Floor
from app.models.location import Location


async def get_locations(
    db: AsyncSession,
) -> list[Location]:
    result = await db.execute(
        select(Location)
        .order_by(Location.name)
    )

    return list(result.scalars().all())


async def get_location_by_id(
    db: AsyncSession,
    location_id: int,
) -> Location | None:
    result = await db.execute(
        select(Location).where(
            Location.id == location_id
        )
    )

    return result.scalar_one_or_none()


async def create_location(
    db: AsyncSession,
    floor_id: int | None,
    name: str,
    location_type: str,
) -> Location:

    # If a floor is provided, make sure it exists
    if floor_id is not None:
        result = await db.execute(
            select(Floor).where(
                Floor.id == floor_id
            )
        )

        floor = result.scalar_one_or_none()

        if floor is None:
            raise ValueError("Floor not found.")

        if not floor.is_active:
            raise ValueError("Floor is inactive.")

    # Prevent duplicate location names
    result = await db.execute(
        select(Location).where(
            Location.name == name,
            Location.floor_id == floor_id,
        )
    )

    existing_location = result.scalar_one_or_none()

    if existing_location is not None:
        raise ValueError(
            "Location already exists in this floor."
        )

    location = Location(
        floor_id=floor_id,
        name=name,
        location_type=location_type,
        is_active=True,
    )

    db.add(location)

    await db.commit()
    await db.refresh(location)

    return location


async def update_location(
    db: AsyncSession,
    location_id: int,
    floor_id: int | None,
    name: str,
    location_type: str,
) -> Location:

    location = await get_location_by_id(
        db,
        location_id,
    )

    if location is None:
        raise ValueError("Location not found.")

    # If a floor is provided, make sure it exists
    if floor_id is not None:
        result = await db.execute(
            select(Floor).where(
                Floor.id == floor_id
            )
        )

        floor = result.scalar_one_or_none()

        if floor is None:
            raise ValueError("Floor not found.")

        if not floor.is_active:
            raise ValueError("Floor is inactive.")

    # Prevent duplicate location names
    result = await db.execute(
        select(Location).where(
            Location.name == name,
            Location.floor_id == floor_id,
            Location.id != location_id,
        )
    )

    existing_location = result.scalar_one_or_none()

    if existing_location is not None:
        raise ValueError(
            "Location already exists in this floor."
        )

    location.floor_id = floor_id
    location.name = name
    location.location_type = location_type

    await db.commit()
    await db.refresh(location)

    return location


async def deactivate_location(
    db: AsyncSession,
    location_id: int,
) -> Location:

    location = await get_location_by_id(
        db,
        location_id,
    )

    if location is None:
        raise ValueError("Location not found.")

    location.is_active = False

    await db.commit()
    await db.refresh(location)

    return location