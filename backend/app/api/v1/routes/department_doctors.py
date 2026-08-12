from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.department_doctor import (
    DepartmentDoctorCreate,
    DepartmentDoctorResponse,
    DepartmentDoctorUpdate,
)
from app.services.department_doctor import (
    create_department_doctor_assignment,
    deactivate_department_doctor_assignment,
    get_department_doctor_assignments,
    update_department_doctor_assignment,
)


router = APIRouter(
    prefix="/department-doctors",
    tags=["Department Doctor Management"],
)


@router.get(
    "",
    response_model=list[DepartmentDoctorResponse],
)
async def list_department_doctor_assignments(
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_department_doctor_assignments(db)


@router.post(
    "",
    response_model=DepartmentDoctorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_doctor_to_department(
    assignment_data: DepartmentDoctorCreate,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_department_doctor_assignment(
            db=db,
            department_id=assignment_data.department_id,
            doctor_id=assignment_data.doctor_id,
            is_primary=assignment_data.is_primary,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail in {
            "Department not found.",
            "Doctor not found.",
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
    "/{assignment_id}",
    response_model=DepartmentDoctorResponse,
)
async def update_department_doctor(
    assignment_id: int,
    assignment_data: DepartmentDoctorUpdate,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_department_doctor_assignment(
            db=db,
            assignment_id=assignment_id,
            is_primary=assignment_data.is_primary,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Assignment not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.patch(
    "/{assignment_id}/deactivate",
    response_model=DepartmentDoctorResponse,
)
async def deactivate_department_doctor(
    assignment_id: int,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await deactivate_department_doctor_assignment(
            db=db,
            assignment_id=assignment_id,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Assignment not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )