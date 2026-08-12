from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.equipment_category import EquipmentCategory


async def get_equipment_categories(
    db: AsyncSession,
) -> list[EquipmentCategory]:
    result = await db.execute(
        select(EquipmentCategory)
        .order_by(EquipmentCategory.name)
    )

    return list(result.scalars().all())


async def get_equipment_category_by_id(
    db: AsyncSession,
    category_id: int,
) -> EquipmentCategory | None:
    result = await db.execute(
        select(EquipmentCategory).where(
            EquipmentCategory.id == category_id
        )
    )

    return result.scalar_one_or_none()


async def create_equipment_category(
    db: AsyncSession,
    name: str,
    description: str | None = None,
) -> EquipmentCategory:

    result = await db.execute(
        select(EquipmentCategory).where(
            EquipmentCategory.name == name
        )
    )

    existing = result.scalar_one_or_none()

    if existing is not None:
        raise ValueError(
            "Equipment category name already exists."
        )

    category = EquipmentCategory(
        name=name,
        description=description,
        is_active=True,
    )

    db.add(category)

    await db.commit()
    await db.refresh(category)

    return category


async def update_equipment_category(
    db: AsyncSession,
    category_id: int,
    name: str,
    description: str | None = None,
) -> EquipmentCategory:

    category = await get_equipment_category_by_id(
        db,
        category_id,
    )

    if category is None:
        raise ValueError(
            "Equipment category not found."
        )

    result = await db.execute(
        select(EquipmentCategory).where(
            EquipmentCategory.name == name,
            EquipmentCategory.id != category_id,
        )
    )

    existing = result.scalar_one_or_none()

    if existing is not None:
        raise ValueError(
            "Equipment category name already exists."
        )

    category.name = name
    category.description = description

    await db.commit()
    await db.refresh(category)

    return category


async def deactivate_equipment_category(
    db: AsyncSession,
    category_id: int,
) -> EquipmentCategory:

    category = await get_equipment_category_by_id(
        db,
        category_id,
    )

    if category is None:
        raise ValueError(
            "Equipment category not found."
        )

    category.is_active = False

    await db.commit()
    await db.refresh(category)

    return category