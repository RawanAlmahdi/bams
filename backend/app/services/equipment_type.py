from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.equipment_category import EquipmentCategory
from app.models.equipment_type import EquipmentType


async def get_equipment_types(
    db: AsyncSession,
) -> list[EquipmentType]:
    result = await db.execute(
        select(EquipmentType)
        .order_by(EquipmentType.name)
    )

    return list(result.scalars().all())


async def get_equipment_type_by_id(
    db: AsyncSession,
    equipment_type_id: int,
) -> EquipmentType | None:
    result = await db.execute(
        select(EquipmentType).where(
            EquipmentType.id == equipment_type_id
        )
    )

    return result.scalar_one_or_none()


async def create_equipment_type(
    db: AsyncSession,
    category_id: int,
    name: str,
    description: str | None,
) -> EquipmentType:

    result = await db.execute(
        select(EquipmentCategory).where(
            EquipmentCategory.id == category_id
        )
    )

    category = result.scalar_one_or_none()

    if category is None:
        raise ValueError(
            "Equipment category not found."
        )

    if not category.is_active:
        raise ValueError(
            "Equipment category is inactive."
        )

    result = await db.execute(
        select(EquipmentType).where(
            EquipmentType.category_id == category_id,
            EquipmentType.name == name,
        )
    )

    if result.scalar_one_or_none() is not None:
        raise ValueError(
            "Equipment type already exists in this category."
        )

    equipment_type = EquipmentType(
        category_id=category_id,
        name=name,
        description=description,
        is_active=True,
    )

    db.add(equipment_type)

    await db.commit()
    await db.refresh(equipment_type)

    return equipment_type


async def update_equipment_type(
    db: AsyncSession,
    equipment_type_id: int,
    category_id: int,
    name: str,
    description: str | None,
) -> EquipmentType:

    equipment_type = await get_equipment_type_by_id(
        db,
        equipment_type_id,
    )

    if equipment_type is None:
        raise ValueError(
            "Equipment type not found."
        )

    result = await db.execute(
        select(EquipmentCategory).where(
            EquipmentCategory.id == category_id
        )
    )

    category = result.scalar_one_or_none()

    if category is None:
        raise ValueError(
            "Equipment category not found."
        )

    if not category.is_active:
        raise ValueError(
            "Equipment category is inactive."
        )

    result = await db.execute(
        select(EquipmentType).where(
            EquipmentType.category_id == category_id,
            EquipmentType.name == name,
            EquipmentType.id != equipment_type_id,
        )
    )

    if result.scalar_one_or_none() is not None:
        raise ValueError(
            "Equipment type already exists in this category."
        )

    equipment_type.category_id = category_id
    equipment_type.name = name
    equipment_type.description = description

    await db.commit()
    await db.refresh(equipment_type)

    return equipment_type


async def deactivate_equipment_type(
    db: AsyncSession,
    equipment_type_id: int,
) -> EquipmentType:

    equipment_type = await get_equipment_type_by_id(
        db,
        equipment_type_id,
    )

    if equipment_type is None:
        raise ValueError(
            "Equipment type not found."
        )

    equipment_type.is_active = False

    await db.commit()
    await db.refresh(equipment_type)

    return equipment_type