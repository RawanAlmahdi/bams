from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.building import Building
from app.models.floor import Floor


async def get_floors(
    db: AsyncSession,
) -> list[Floor]:
    result = await db.execute(
        select(Floor)
        .order_by(Floor.building_id, Floor.floor_label)
    )

    return list(result.scalars().all())


async def get_floor_by_id(
    db: AsyncSession,
    floor_id: int,
) -> Floor | None:
    result = await db.execute(
        select(Floor).where(Floor.id == floor_id)
    )

    return result.scalar_one_or_none()


async def create_floor(
    db: AsyncSession,
    building_id: int,
    floor_label: str,
) -> Floor:
    # Make sure the building exists
    result = await db.execute(
        select(Building).where(
            Building.id == building_id
        )
    )

    building = result.scalar_one_or_none()

    if building is None:
        raise ValueError("Building not found.")

    if not building.is_active:
        raise ValueError("Building is inactive.")

    # Prevent duplicate floor labels inside the same building
    result = await db.execute(
        select(Floor).where(
            Floor.building_id == building_id,
            Floor.floor_label == floor_label,
        )
    )

    existing_floor = result.scalar_one_or_none()

    if existing_floor is not None:
        raise ValueError(
            "Floor already exists in this building."
        )

    floor = Floor(
        building_id=building_id,
        floor_label=floor_label,
        is_active=True,
    )

    db.add(floor)

    await db.commit()
    await db.refresh(floor)

    return floor


async def update_floor(
    db: AsyncSession,
    floor_id: int,
    building_id: int,
    floor_label: str,
) -> Floor:
    floor = await get_floor_by_id(
        db,
        floor_id,
    )

    if floor is None:
        raise ValueError("Floor not found.")

    # Make sure the new building exists
    result = await db.execute(
        select(Building).where(
            Building.id == building_id
        )
    )

    building = result.scalar_one_or_none()

    if building is None:
        raise ValueError("Building not found.")

    if not building.is_active:
        raise ValueError("Building is inactive.")

    # Prevent duplicate floor labels
    result = await db.execute(
        select(Floor).where(
            Floor.building_id == building_id,
            Floor.floor_label == floor_label,
            Floor.id != floor_id,
        )
    )

    existing_floor = result.scalar_one_or_none()

    if existing_floor is not None:
        raise ValueError(
            "Floor already exists in this building."
        )

    floor.building_id = building_id
    floor.floor_label = floor_label

    await db.commit()
    await db.refresh(floor)

    return floor


async def deactivate_floor(
    db: AsyncSession,
    floor_id: int,
) -> Floor:
    floor = await get_floor_by_id(
        db,
        floor_id,
    )

    if floor is None:
        raise ValueError("Floor not found.")

    floor.is_active = False

    await db.commit()
    await db.refresh(floor)

    return floor