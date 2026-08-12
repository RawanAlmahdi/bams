from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.floor import (
    FloorCreate,
    FloorResponse,
    FloorUpdate,
)
from app.services.floor import (
    create_floor,
    deactivate_floor,
    get_floor_by_id,
    get_floors,
    update_floor,
)

router = APIRouter(
    prefix="/floors",
    tags=["Floor Management"],
)


@router.get(
    "",
    response_model=list[FloorResponse],
)
async def list_floors(
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_floors(db)


@router.get(
    "/{floor_id}",
    response_model=FloorResponse,
)
async def get_floor(
    floor_id: int,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    floor = await get_floor_by_id(
        db,
        floor_id,
    )

    if floor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Floor not found.",
        )

    return floor


@router.post(
    "",
    response_model=FloorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_floor(
    floor_data: FloorCreate,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_floor(
            db=db,
            building_id=floor_data.building_id,
            floor_label=floor_data.floor_label,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Building not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.patch(
    "/{floor_id}",
    response_model=FloorResponse,
)
async def edit_floor(
    floor_id: int,
    floor_data: FloorUpdate,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_floor(
            db=db,
            floor_id=floor_id,
            building_id=floor_data.building_id,
            floor_label=floor_data.floor_label,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail in {
            "Floor not found.",
            "Building not found.",
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
    "/{floor_id}/deactivate",
    response_model=FloorResponse,
)
async def deactivate_floor_endpoint(
    floor_id: int,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await deactivate_floor(
            db=db,
            floor_id=floor_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )