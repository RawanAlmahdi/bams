from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.equipment_type import (
    EquipmentTypeCreate,
    EquipmentTypeResponse,
    EquipmentTypeUpdate,
)
from app.services.equipment_type import (
    create_equipment_type,
    deactivate_equipment_type,
    get_equipment_type_by_id,
    get_equipment_types,
    update_equipment_type,
)


router = APIRouter(
    prefix="/equipment-types",
    tags=["Equipment Type Management"],
)


ALLOWED_ROLES = (
    "System Administrator",
    "Biomedical Engineer",
)


@router.get(
    "",
    response_model=list[EquipmentTypeResponse],
)
async def list_equipment_types(
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_equipment_types(db)


@router.get(
    "/{equipment_type_id}",
    response_model=EquipmentTypeResponse,
)
async def get_equipment_type(
    equipment_type_id: int,
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    equipment_type = await get_equipment_type_by_id(
        db,
        equipment_type_id,
    )

    if equipment_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment type not found.",
        )

    return equipment_type


@router.post(
    "",
    response_model=EquipmentTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_equipment_type(
    equipment_type_data: EquipmentTypeCreate,
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_equipment_type(
            db=db,
            category_id=equipment_type_data.category_id,
            name=equipment_type_data.name,
            description=equipment_type_data.description,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Equipment category not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.patch(
    "/{equipment_type_id}",
    response_model=EquipmentTypeResponse,
)
async def edit_equipment_type(
    equipment_type_id: int,
    equipment_type_data: EquipmentTypeUpdate,
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_equipment_type(
            db=db,
            equipment_type_id=equipment_type_id,
            category_id=equipment_type_data.category_id,
            name=equipment_type_data.name,
            description=equipment_type_data.description,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail in {
            "Equipment type not found.",
            "Equipment category not found.",
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
    "/{equipment_type_id}/deactivate",
    response_model=EquipmentTypeResponse,
)
async def deactivate_equipment_type_route(
    equipment_type_id: int,
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await deactivate_equipment_type(
            db=db,
            equipment_type_id=equipment_type_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )