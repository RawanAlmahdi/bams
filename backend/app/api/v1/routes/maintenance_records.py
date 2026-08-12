from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.maintenance_record import (
    MaintenanceRecordCreate,
    MaintenanceRecordResponse,
    MaintenanceRecordUpdate,
)
from app.services.maintenance_record import (
    complete_maintenance_record,
    create_maintenance_record,
    get_maintenance_record_by_id,
    get_maintenance_records,
    update_maintenance_record,
)


router = APIRouter(
    prefix="/maintenance-records",
    tags=["Maintenance Record Management"],
)


ENGINEER_ROLES = (
    "Biomedical Engineer",
    "Senior Biomedical Engineer",
)


@router.get(
    "",
    response_model=list[MaintenanceRecordResponse],
)
async def list_maintenance_records(
    current_user: User = Depends(
        require_role(*ENGINEER_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_maintenance_records(db)


@router.get(
    "/{record_id}",
    response_model=MaintenanceRecordResponse,
)
async def get_maintenance_record(
    record_id: int,
    current_user: User = Depends(
        require_role(*ENGINEER_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    record = await get_maintenance_record_by_id(
        db,
        record_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance record not found.",
        )

    return record


@router.post(
    "/request/{maintenance_request_id}",
    response_model=MaintenanceRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_record(
    maintenance_request_id: int,
    record_data: MaintenanceRecordCreate,
    current_user: User = Depends(
        require_role(*ENGINEER_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_maintenance_record(
            db=db,
            maintenance_request_id=maintenance_request_id,
            engineer=current_user,
            work_description=record_data.work_description,
            findings=record_data.findings,
            recommendations=record_data.recommendations,
            cost=record_data.cost,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail in {
            "Maintenance request not found.",
            "Only the assigned engineer can create this record.",
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
    "/{record_id}",
    response_model=MaintenanceRecordResponse,
)
async def update_record(
    record_id: int,
    record_data: MaintenanceRecordUpdate,
    current_user: User = Depends(
        require_role(*ENGINEER_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_maintenance_record(
            db=db,
            record_id=record_id,
            engineer=current_user,
            work_description=record_data.work_description,
            findings=record_data.findings,
            recommendations=record_data.recommendations,
            cost=record_data.cost,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Maintenance record not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


@router.patch(
    "/{record_id}/complete",
    response_model=MaintenanceRecordResponse,
)
async def complete_record(
    record_id: int,
    current_user: User = Depends(
        require_role(*ENGINEER_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await complete_maintenance_record(
            db=db,
            record_id=record_id,
            engineer=current_user,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Maintenance record not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )