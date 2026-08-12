from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.machine import (
    MachineCreate,
    MachineResponse,
    MachineUpdate,
)
from app.services.machine import (
    create_machine,
    deactivate_machine,
    get_machine_by_id,
    get_machines,
    update_machine,
)


router = APIRouter(
    prefix="/machines",
    tags=["Machine Management"],
)


@router.get(
    "",
    response_model=list[MachineResponse],
)
async def list_machines(
    current_user: User = Depends(
        require_role("System Administrator", "Biomedical Engineer")
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_machines(db)


@router.get(
    "/{machine_id}",
    response_model=MachineResponse,
)
async def get_machine(
    machine_id: int,
    current_user: User = Depends(
        require_role("System Administrator", "Biomedical Engineer")
    ),
    db: AsyncSession = Depends(get_db),
):
    machine = await get_machine_by_id(
        db,
        machine_id,
    )

    if machine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found.",
        )

    return machine


@router.post(
    "",
    response_model=MachineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_machine(
    machine_data: MachineCreate,
    current_user: User = Depends(
        require_role("System Administrator", "Biomedical Engineer")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_machine(
            db=db,
            serial_number=machine_data.serial_number,
            asset_tag=machine_data.asset_tag,
            name=machine_data.name,
            model=machine_data.model,
            manufacturer_id=machine_data.manufacturer_id,
            equipment_type_id=machine_data.equipment_type_id,
            location_id=machine_data.location_id,
            status=machine_data.status,
            condition=machine_data.condition,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail in {
            "Location not found.",
        }:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.patch(
    "/{machine_id}",
    response_model=MachineResponse,
)
async def edit_machine(
    machine_id: int,
    machine_data: MachineUpdate,
    current_user: User = Depends(
        require_role("System Administrator", "Biomedical Engineer")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_machine(
            db=db,
            machine_id=machine_id,
            asset_tag=machine_data.asset_tag,
            name=machine_data.name,
            model=machine_data.model,
            manufacturer_id=machine_data.manufacturer_id,
            equipment_type_id=machine_data.equipment_type_id,
            location_id=machine_data.location_id,
            status=machine_data.status,
            condition=machine_data.condition,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Machine not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.patch(
    "/{machine_id}/deactivate",
    response_model=MachineResponse,
)
async def deactivate_machine_route(
    machine_id: int,
    current_user: User = Depends(
        require_role("System Administrator", "Biomedical Engineer")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await deactivate_machine(
            db=db,
            machine_id=machine_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )