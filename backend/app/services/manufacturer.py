from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.manufacturer import Manufacturer


async def get_manufacturers(
    db: AsyncSession,
) -> list[Manufacturer]:
    result = await db.execute(
        select(Manufacturer).order_by(Manufacturer.name)
    )

    return list(result.scalars().all())


async def get_manufacturer_by_id(
    db: AsyncSession,
    manufacturer_id: int,
) -> Manufacturer | None:
    result = await db.execute(
        select(Manufacturer).where(
            Manufacturer.id == manufacturer_id
        )
    )

    return result.scalar_one_or_none()


async def create_manufacturer(
    db: AsyncSession,
    name: str,
) -> Manufacturer:

    result = await db.execute(
        select(Manufacturer).where(
            Manufacturer.name == name
        )
    )

    if result.scalar_one_or_none() is not None:
        raise ValueError(
            "Manufacturer name already exists."
        )

    manufacturer = Manufacturer(
        name=name,
        is_active=True,
    )

    db.add(manufacturer)

    await db.commit()
    await db.refresh(manufacturer)

    return manufacturer


async def update_manufacturer(
    db: AsyncSession,
    manufacturer_id: int,
    name: str,
) -> Manufacturer:

    manufacturer = await get_manufacturer_by_id(
        db,
        manufacturer_id,
    )

    if manufacturer is None:
        raise ValueError(
            "Manufacturer not found."
        )

    result = await db.execute(
        select(Manufacturer).where(
            Manufacturer.name == name,
            Manufacturer.id != manufacturer_id,
        )
    )

    if result.scalar_one_or_none() is not None:
        raise ValueError(
            "Manufacturer name already exists."
        )

    manufacturer.name = name

    await db.commit()
    await db.refresh(manufacturer)

    return manufacturer


async def deactivate_manufacturer(
    db: AsyncSession,
    manufacturer_id: int,
) -> Manufacturer:

    manufacturer = await get_manufacturer_by_id(
        db,
        manufacturer_id,
    )

    if manufacturer is None:
        raise ValueError(
            "Manufacturer not found."
        )

    manufacturer.is_active = False

    await db.commit()
    await db.refresh(manufacturer)

    return manufacturer