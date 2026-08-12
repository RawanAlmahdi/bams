from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.maintenance_record import MaintenanceRecord
from app.models.maintenance_request import MaintenanceRequest
from app.models.user import User


def json_cost(value):
    if value is None:
        return None

    return float(value)


async def get_maintenance_records(
    db: AsyncSession,
) -> list[MaintenanceRecord]:
    result = await db.execute(
        select(MaintenanceRecord).order_by(
            MaintenanceRecord.started_at.desc()
        )
    )

    return list(result.scalars().all())


async def get_maintenance_record_by_id(
    db: AsyncSession,
    record_id: int,
) -> MaintenanceRecord | None:
    result = await db.execute(
        select(MaintenanceRecord).where(
            MaintenanceRecord.id == record_id
        )
    )

    return result.scalar_one_or_none()


async def get_record_for_request(
    db: AsyncSession,
    maintenance_request_id: int,
) -> MaintenanceRecord | None:
    result = await db.execute(
        select(MaintenanceRecord).where(
            MaintenanceRecord.maintenance_request_id
            == maintenance_request_id
        )
    )

    return result.scalar_one_or_none()


async def create_maintenance_record(
    db: AsyncSession,
    maintenance_request_id: int,
    engineer: User,
    work_description: str,
    findings: str | None,
    recommendations: str | None,
    cost,
) -> MaintenanceRecord:

    result = await db.execute(
        select(MaintenanceRequest).where(
            MaintenanceRequest.id == maintenance_request_id
        )
    )

    request = result.scalar_one_or_none()

    if request is None:
        raise ValueError(
            "Maintenance request not found."
        )

    if request.assigned_to != engineer.id:
        raise ValueError(
            "Only the assigned engineer can create this record."
        )

    if request.status != "IN_PROGRESS":
        raise ValueError(
            "Maintenance request must be in progress."
        )

    existing_record = await get_record_for_request(
        db,
        maintenance_request_id,
    )

    if existing_record is not None:
        raise ValueError(
            "A maintenance record already exists for this request."
        )

    record = MaintenanceRecord(
        maintenance_request_id=maintenance_request_id,
        performed_by=engineer.id,
        started_at=datetime.utcnow(),
        completed_at=None,
        work_description=work_description,
        findings=findings,
        recommendations=recommendations,
        cost=cost,
    )

    db.add(record)

    await db.flush()

    db.add(
        AuditLog(
            user_id=engineer.id,
            action="CREATE",
            entity_type="MaintenanceRecord",
            entity_id=record.id,
            description="Maintenance record created.",
            old_values=None,
            new_values={
                "maintenance_request_id": maintenance_request_id,
                "performed_by": engineer.id,
                "cost": json_cost(cost),
            },
        )
    )

    await db.commit()
    await db.refresh(record)

    return record


async def update_maintenance_record(
    db: AsyncSession,
    record_id: int,
    engineer: User,
    work_description: str,
    findings: str | None,
    recommendations: str | None,
    cost,
) -> MaintenanceRecord:

    record = await get_maintenance_record_by_id(
        db,
        record_id,
    )

    if record is None:
        raise ValueError(
            "Maintenance record not found."
        )

    if record.performed_by != engineer.id:
        raise ValueError(
            "Only the engineer who created this record can update it."
        )

    if record.completed_at is not None:
        raise ValueError(
            "Completed maintenance records cannot be updated."
        )

    old_values = {
        "work_description": record.work_description,
        "findings": record.findings,
        "recommendations": record.recommendations,
        "cost": json_cost(record.cost),
    }

    record.work_description = work_description
    record.findings = findings
    record.recommendations = recommendations
    record.cost = cost

    db.add(
        AuditLog(
            user_id=engineer.id,
            action="UPDATE",
            entity_type="MaintenanceRecord",
            entity_id=record.id,
            description="Maintenance record updated.",
            old_values=old_values,
            new_values={
                "work_description": work_description,
                "findings": findings,
                "recommendations": recommendations,
                "cost": json_cost(cost),
            },
        )
    )

    await db.commit()
    await db.refresh(record)

    return record


async def complete_maintenance_record(
    db: AsyncSession,
    record_id: int,
    engineer: User,
) -> MaintenanceRecord:

    record = await get_maintenance_record_by_id(
        db,
        record_id,
    )

    if record is None:
        raise ValueError(
            "Maintenance record not found."
        )

    if record.performed_by != engineer.id:
        raise ValueError(
            "Only the engineer who created this record can complete it."
        )

    if record.completed_at is not None:
        raise ValueError(
            "Maintenance record is already completed."
        )

    completed_at = datetime.utcnow()

    record.completed_at = completed_at

    result = await db.execute(
        select(MaintenanceRequest).where(
            MaintenanceRequest.id
            == record.maintenance_request_id
        )
    )

    request = result.scalar_one()

    request.status = "COMPLETED"
    request.completed_at = completed_at

    db.add(
        AuditLog(
            user_id=engineer.id,
            action="COMPLETE",
            entity_type="MaintenanceRecord",
            entity_id=record.id,
            description=(
                "Maintenance record and maintenance request "
                "completed."
            ),
            old_values={
                "record_completed_at": None,
                "request_status": "IN_PROGRESS",
            },
            new_values={
                "record_completed_at": completed_at.isoformat(),
                "request_status": "COMPLETED",
            },
        )
    )

    await db.commit()
    await db.refresh(record)

    return record