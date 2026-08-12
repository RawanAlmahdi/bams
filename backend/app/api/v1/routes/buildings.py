from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.building import (
    BuildingCreate,
    BuildingResponse,
    BuildingUpdate,
)
from app.services.building import (
    create_building,
    deactivate_building,
    get_building_by_id,
    get_buildings,
    update_building,
)

router = APIRouter(
    prefix="/buildings",
    tags=["Building Management"],
)


@router.get(
    "",
    response_model=list[BuildingResponse],
)
async def list_buildings(
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_buildings(db)


@router.get(
    "/{building_id}",
    response_model=BuildingResponse,
)
async def get_building(
    building_id: int,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    building = await get_building_by_id(
        db,
        building_id,
    )

    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Building not found.",
        )

    return building


@router.post(
    "",
    response_model=BuildingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_building(
    building_data: BuildingCreate,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_building(
            db=db,
            name=building_data.name,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.patch(
    "/{building_id}",
    response_model=BuildingResponse,
)
async def edit_building(
    building_id: int,
    building_data: BuildingUpdate,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_building(
            db=db,
            building_id=building_id,
            name=building_data.name,
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
    "/{building_id}/deactivate",
    response_model=BuildingResponse,
)
async def deactivate_building_endpoint(
    building_id: int,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await deactivate_building(
            db=db,
            building_id=building_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )