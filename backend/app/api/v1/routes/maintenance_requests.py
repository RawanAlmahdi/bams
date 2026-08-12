from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.maintenance_request import (
    MaintenanceRequestCreate,
    MaintenanceRequestResponse,
)
from app.services.maintenance_request import (
    create_maintenance_request,
    complete_maintenance_request,
    get_maintenance_request_by_id,
    get_maintenance_requests,
    release_maintenance_request,
    reassign_maintenance_request,
    start_maintenance_request,
    take_maintenance_request,
)


router = APIRouter(
    prefix="/maintenance-requests",
    tags=["Maintenance Request Management"],
)


REQUESTER_ROLES = (
    "Technician",
    "Doctor",
    "RPD Doctor",
    "Nurse",
)

ENGINEER_ROLES = (
    "Biomedical Engineer",
    "Senior Biomedical Engineer",
)


@router.post(
    "",
    response_model=MaintenanceRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_request(
    request_data: MaintenanceRequestCreate,
    current_user: User = Depends(
        require_role(*REQUESTER_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await create_maintenance_request(
            db=db,
            machine_id=request_data.machine_id,
            requested_by=current_user,
            request_type=request_data.request_type,
            priority=request_data.priority,
            problem_description=request_data.problem_description,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail in {
            "Machine not found.",
            "Machine is inactive.",
        }:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.get(
    "",
    response_model=list[MaintenanceRequestResponse],
)
async def list_requests(
    current_user: User = Depends(
        require_role(*ENGINEER_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_maintenance_requests(db)


@router.get(
    "/{request_id}",
    response_model=MaintenanceRequestResponse,
)
async def get_request(
    request_id: int,
    current_user: User = Depends(
        require_role(
            *REQUESTER_ROLES,
            *ENGINEER_ROLES,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    request = await get_maintenance_request_by_id(
        db,
        request_id,
    )

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance request not found.",
        )

    return request


@router.patch(
    "/{request_id}/take",
    response_model=MaintenanceRequestResponse,
)
async def take_request(
    request_id: int,
    current_user: User = Depends(
        require_role(*ENGINEER_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await take_maintenance_request(
            db=db,
            request_id=request_id,
            engineer=current_user,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Maintenance request not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.patch(
    "/{request_id}/start",
    response_model=MaintenanceRequestResponse,
)
async def start_request(
    request_id: int,
    current_user: User = Depends(
        require_role(*ENGINEER_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await start_maintenance_request(
            db=db,
            request_id=request_id,
            engineer=current_user,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Maintenance request not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.patch(
    "/{request_id}/release",
    response_model=MaintenanceRequestResponse,
)
async def release_request(
    request_id: int,
    current_user: User = Depends(
        require_role(*ENGINEER_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await release_maintenance_request(
            db=db,
            request_id=request_id,
            engineer=current_user,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Maintenance request not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


@router.patch(
    "/{request_id}/reassign/{new_engineer_id}",
    response_model=MaintenanceRequestResponse,
)
async def reassign_request(
    request_id: int,
    new_engineer_id: int,
    current_user: User = Depends(
        require_role("Senior Biomedical Engineer")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await reassign_maintenance_request(
            db=db,
            request_id=request_id,
            senior_engineer=current_user,
            new_engineer_id=new_engineer_id,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail in {
            "Maintenance request not found.",
            "Engineer not found.",
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
    "/{request_id}/complete",
    response_model=MaintenanceRequestResponse,
)
async def complete_request(
    request_id: int,
    current_user: User = Depends(
        require_role(*ENGINEER_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await complete_maintenance_request(
            db=db,
            request_id=request_id,
            engineer=current_user,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "Maintenance request not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )