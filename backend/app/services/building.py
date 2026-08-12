from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.building import Building


async def get_buildings(
    db: AsyncSession,
) -> list[Building]:
    result = await db.execute(
        select(Building)
        .order_by(Building.name)
    )

    return list(result.scalars().all())


async def get_building_by_id(
    db: AsyncSession,
    building_id: int,
) -> Building | None:
    result = await db.execute(
        select(Building).where(
            Building.id == building_id
        )
    )

    return result.scalar_one_or_none()


async def create_building(
    db: AsyncSession,
    name: str,
) -> Building:
    result = await db.execute(
        select(Building).where(
            Building.name == name
        )
    )

    existing_building = result.scalar_one_or_none()

    if existing_building is not None:
        raise ValueError("Building already exists.")

    building = Building(
        name=name,
        is_active=True,
    )

    db.add(building)

    await db.commit()
    await db.refresh(building)

    return building


async def update_building(
    db: AsyncSession,
    building_id: int,
    name: str,
) -> Building:
    building = await get_building_by_id(
        db,
        building_id,
    )

    if building is None:
        raise ValueError("Building not found.")

    result = await db.execute(
        select(Building).where(
            Building.name == name,
            Building.id != building_id,
        )
    )

    existing_building = result.scalar_one_or_none()

    if existing_building is not None:
        raise ValueError("Building already exists.")

    building.name = name

    await db.commit()
    await db.refresh(building)

    return building


async def deactivate_building(
    db: AsyncSession,
    building_id: int,
) -> Building:
    building = await get_building_by_id(
        db,
        building_id,
    )

    if building is None:
        raise ValueError("Building not found.")

    building.is_active = False

    await db.commit()
    await db.refresh(building)

    return building