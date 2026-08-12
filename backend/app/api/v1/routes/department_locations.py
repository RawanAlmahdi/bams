from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.department_location import (
    DepartmentLocationCreate,
    DepartmentLocationResponse,
)
from app.services.department_location import (
    create_department_location,
    delete_department_location,
    get_department_locations,
)

router = APIRouter(
    prefix="/department-locations",
    tags=["Department Location Management"],
)


@router.get(
    "",
    response_model=list[DepartmentLocationResponse],
)
async def list_department_locations(
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_department_locations(db)


@router.post(
    "",
    response_model=DepartmentLocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_department_location(
    assignment_data: DepartmentLocationCreate,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_department_location(
            db=db,
            department_id=assignment_data.department_id,
            location_id=assignment_data.location_id,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail in {
            "Department not found.",
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


@router.delete(
    "/{department_location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_department_location(
    department_location_id: int,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        await delete_department_location(
            db=db,
            department_location_id=department_location_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )