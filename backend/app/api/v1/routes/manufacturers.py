from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.manufacturer import (
    ManufacturerCreate,
    ManufacturerResponse,
    ManufacturerUpdate,
)
from app.services.manufacturer import (
    create_manufacturer,
    deactivate_manufacturer,
    get_manufacturer_by_id,
    get_manufacturers,
    update_manufacturer,
)


router = APIRouter(
    prefix="/manufacturers",
    tags=["Manufacturer Management"],
)


ALLOWED_ROLES = (
    "System Administrator",
    "Biomedical Engineer",
)


@router.get(
    "",
    response_model=list[ManufacturerResponse],
)
async def list_manufacturers(
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_manufacturers(db)


@router.get(
    "/{manufacturer_id}",
    response_model=ManufacturerResponse,
)
async def get_manufacturer(
    manufacturer_id: int,
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    manufacturer = await get_manufacturer_by_id(
        db,
        manufacturer_id,
    )

    if manufacturer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manufacturer not found.",
        )

    return manufacturer


@router.post(
    "",
    response_model=ManufacturerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_manufacturer(
    manufacturer_data: ManufacturerCreate,
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_manufacturer(
            db=db,
            name=manufacturer_data.name,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.patch(
    "/{manufacturer_id}",
    response_model=ManufacturerResponse,
)
async def edit_manufacturer(
    manufacturer_id: int,
    manufacturer_data: ManufacturerUpdate,
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_manufacturer(
            db=db,
            manufacturer_id=manufacturer_id,
            name=manufacturer_data.name,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Manufacturer not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.patch(
    "/{manufacturer_id}/deactivate",
    response_model=ManufacturerResponse,
)
async def deactivate_manufacturer_route(
    manufacturer_id: int,
    current_user: User = Depends(
        require_role(*ALLOWED_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await deactivate_manufacturer(
            db=db,
            manufacturer_id=manufacturer_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )