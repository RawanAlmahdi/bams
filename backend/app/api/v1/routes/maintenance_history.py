from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.maintenance_history import (
    MaintenanceHistoryItem,
)
from app.services.maintenance_history import (
    get_machine_maintenance_history,
)


router = APIRouter(
    prefix="/machines",
    tags=["Maintenance History"],
)


ENGINEER_ROLES = (
    "Biomedical Engineer",
    "Senior Biomedical Engineer",
)


@router.get(
    "/{machine_id}/maintenance-history",
    response_model=list[MaintenanceHistoryItem],
)
async def get_maintenance_history(
    machine_id: int,
    current_user: User = Depends(
        require_role(*ENGINEER_ROLES)
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_machine_maintenance_history(
        db=db,
        machine_id=machine_id,
    )