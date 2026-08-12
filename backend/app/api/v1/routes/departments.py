from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)
from app.services.department import (
    create_department,
    deactivate_department,
    get_department_by_id,
    get_departments,
    update_department,
)

router = APIRouter(
    prefix="/departments",
    tags=["Department Management"],
)


@router.get(
    "",
    response_model=list[DepartmentResponse],
)
async def list_departments(
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_departments(db)


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
)
async def get_department(
    department_id: int,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    department = await get_department_by_id(
        db,
        department_id,
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found.",
        )

    return department


@router.post(
    "",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_department(
    department_data: DepartmentCreate,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_department(
            db=db,
            name=department_data.name,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.patch(
    "/{department_id}",
    response_model=DepartmentResponse,
)
async def edit_department(
    department_id: int,
    department_data: DepartmentUpdate,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_department(
            db=db,
            department_id=department_id,
            name=department_data.name,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Department not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.patch(
    "/{department_id}/deactivate",
    response_model=DepartmentResponse,
)
async def deactivate_department_route(
    department_id: int,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await deactivate_department(
            db=db,
            department_id=department_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )