from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.equipment_category import (
    EquipmentCategoryCreate,
    EquipmentCategoryResponse,
    EquipmentCategoryUpdate,
)
from app.services.equipment_category import (
    create_equipment_category,
    deactivate_equipment_category,
    get_equipment_categories,
    get_equipment_category_by_id,
    update_equipment_category,
)


router = APIRouter(
    prefix="/equipment-categories",
    tags=["Equipment Category Management"],
)


ALLOWED_ROLES = (
    "System Administrator",
    "Biomedical Engineer",
)


@router.get(
    "",
    response_model=list[EquipmentCategoryResponse],
)
async def list_equipment_categories(
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_equipment_categories(db)


@router.get(
    "/{category_id}",
    response_model=EquipmentCategoryResponse,
)
async def get_equipment_category(
    category_id: int,
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    category = await get_equipment_category_by_id(
        db,
        category_id,
    )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment category not found.",
        )

    return category


@router.post(
    "",
    response_model=EquipmentCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_equipment_category(
    category_data: EquipmentCategoryCreate,
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_equipment_category(
            db=db,
            name=category_data.name,
            description=category_data.description,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.patch(
    "/{category_id}",
    response_model=EquipmentCategoryResponse,
)
async def edit_equipment_category(
    category_id: int,
    category_data: EquipmentCategoryUpdate,
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_equipment_category(
            db=db,
            category_id=category_id,
            name=category_data.name,
            description=category_data.description,
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
    "/{category_id}/deactivate",
    response_model=EquipmentCategoryResponse,
)
async def deactivate_equipment_category_route(
    category_id: int,
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await deactivate_equipment_category(
            db=db,
            category_id=category_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )