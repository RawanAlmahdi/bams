from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.models.machine import Machine


async def get_machines(
    db: AsyncSession,
) -> list[Machine]:
    result = await db.execute(
        select(Machine)
        .order_by(Machine.name)
    )

    return list(result.scalars().all())


async def get_machine_by_id(
    db: AsyncSession,
    machine_id: int,
) -> Machine | None:
    result = await db.execute(
        select(Machine).where(
            Machine.id == machine_id
        )
    )

    return result.scalar_one_or_none()


async def create_machine(
    db: AsyncSession,
    serial_number: str,
    asset_tag: str | None,
    name: str,
    model: str | None,
    manufacturer_id: int | None,
    equipment_type_id: int | None,
    location_id: int | None,
    status: str,
    condition: str,
) -> Machine:

    # Serial number must be unique
    result = await db.execute(
        select(Machine).where(
            Machine.serial_number == serial_number
        )
    )

    if result.scalar_one_or_none() is not None:
        raise ValueError(
            "Serial number already exists."
        )

    # Asset tag must be unique when provided
    if asset_tag is not None:
        result = await db.execute(
            select(Machine).where(
                Machine.asset_tag == asset_tag
            )
        )

        if result.scalar_one_or_none() is not None:
            raise ValueError(
                "Asset tag already exists."
            )

    # Validate location when provided
    if location_id is not None:
        result = await db.execute(
            select(Location).where(
                Location.id == location_id
            )
        )

        location = result.scalar_one_or_none()

        if location is None:
            raise ValueError(
                "Location not found."
            )

        if not location.is_active:
            raise ValueError(
                "Location is inactive."
            )

    machine = Machine(
        serial_number=serial_number,
        asset_tag=asset_tag,
        name=name,
        model=model,
        manufacturer_id=manufacturer_id,
        equipment_type_id=equipment_type_id,
        location_id=location_id,
        status=status,
        condition=condition,
        is_active=True,
    )

    db.add(machine)

    await db.commit()
    await db.refresh(machine)

    return machine


async def update_machine(
    db: AsyncSession,
    machine_id: int,
    asset_tag: str | None,
    name: str,
    model: str | None,
    manufacturer_id: int | None,
    equipment_type_id: int | None,
    location_id: int | None,
    status: str,
    condition: str,
) -> Machine:

    machine = await get_machine_by_id(
        db,
        machine_id,
    )

    if machine is None:
        raise ValueError(
            "Machine not found."
        )

    # Asset tag uniqueness
    if asset_tag is not None:
        result = await db.execute(
            select(Machine).where(
                Machine.asset_tag == asset_tag,
                Machine.id != machine_id,
            )
        )

        if result.scalar_one_or_none() is not None:
            raise ValueError(
                "Asset tag already exists."
            )

    # Validate location
    if location_id is not None:
        result = await db.execute(
            select(Location).where(
                Location.id == location_id
            )
        )

        location = result.scalar_one_or_none()

        if location is None:
            raise ValueError(
                "Location not found."
            )

        if not location.is_active:
            raise ValueError(
                "Location is inactive."
            )

    machine.asset_tag = asset_tag
    machine.name = name
    machine.model = model
    machine.manufacturer_id = manufacturer_id
    machine.equipment_type_id = equipment_type_id
    machine.location_id = location_id
    machine.status = status
    machine.condition = condition

    await db.commit()
    await db.refresh(machine)

    return machine


async def deactivate_machine(
    db: AsyncSession,
    machine_id: int,
) -> Machine:

    machine = await get_machine_by_id(
        db,
        machine_id,
    )

    if machine is None:
        raise ValueError(
            "Machine not found."
        )

    machine.is_active = False

    await db.commit()
    await db.refresh(machine)

    return machine