from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance_record import MaintenanceRecord
from app.models.maintenance_request import MaintenanceRequest


async def get_machine_maintenance_history(
    db: AsyncSession,
    machine_id: int,
):
    result = await db.execute(
        select(
            MaintenanceRecord,
            MaintenanceRequest,
        )
        .join(
            MaintenanceRequest,
            MaintenanceRecord.maintenance_request_id
            == MaintenanceRequest.id,
        )
        .where(
            MaintenanceRequest.machine_id == machine_id,
            MaintenanceRecord.completed_at.is_not(None),
        )
        .order_by(
            MaintenanceRecord.completed_at.desc()
        )
    )

    history = []

    for record, request in result.all():
        history.append(
            {
                "maintenance_record_id": record.id,
                "maintenance_request_id": request.id,
                "request_type": request.request_type,
                "priority": request.priority,
                "performed_by": record.performed_by,
                "started_at": record.started_at,
                "completed_at": record.completed_at,
                "problem_description": (
                    request.problem_description
                ),
                "work_description": record.work_description,
                "findings": record.findings,
                "recommendations": record.recommendations,
                "cost": record.cost,
            }
        )

    return history