from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.location import (
    LocationCreate,
    LocationResponse,
    LocationUpdate,
)
from app.services.location import (
    create_location,
    deactivate_location,
    get_location_by_id,
    get_locations,
    update_location,
)

router = APIRouter(
    prefix="/locations",
    tags=["Location Management"],
)


@router.get(
    "",
    response_model=list[LocationResponse],
)
async def list_locations(
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_locations(db)


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
)
async def get_location(
    location_id: int,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    location = await get_location_by_id(
        db,
        location_id,
    )

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found.",
        )

    return location


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_location(
    location_data: LocationCreate,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_location(
            db=db,
            floor_id=location_data.floor_id,
            name=location_data.name,
            location_type=location_data.location_type,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Floor not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.patch(
    "/{location_id}",
    response_model=LocationResponse,
)
async def edit_location(
    location_id: int,
    location_data: LocationUpdate,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_location(
            db=db,
            location_id=location_id,
            floor_id=location_data.floor_id,
            name=location_data.name,
            location_type=location_data.location_type,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail in {
            "Location not found.",
            "Floor not found.",
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
    "/{location_id}/deactivate",
    response_model=LocationResponse,
)
async def deactivate_location_endpoint(
    location_id: int,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await deactivate_location(
            db=db,
            location_id=location_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )