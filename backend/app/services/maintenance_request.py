from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.constants.notification_types import NotificationType
from app.models.audit_log import AuditLog
from app.models.machine import Machine
from app.models.maintenance_request import MaintenanceRequest
from app.models.user import User
from app.services.notification import create_notification


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


async def get_maintenance_requests(
    db: AsyncSession,
) -> list[MaintenanceRequest]:
    result = await db.execute(
        select(MaintenanceRequest).order_by(
            MaintenanceRequest.requested_at.desc()
        )
    )

    return list(result.scalars().all())


async def get_maintenance_request_by_id(
    db: AsyncSession,
    request_id: int,
) -> MaintenanceRequest | None:
    result = await db.execute(
        select(MaintenanceRequest).where(
            MaintenanceRequest.id == request_id
        )
    )

    return result.scalar_one_or_none()


async def get_active_engineers(
    db: AsyncSession,
) -> list[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.is_active.is_(True))
    )

    users = result.scalars().all()

    return [
        user
        for user in users
        if user.role is not None
        and user.role.name in ENGINEER_ROLES
    ]


async def create_maintenance_request(
    db: AsyncSession,
    machine_id: int,
    requested_by: User,
    request_type: str,
    priority: str,
    problem_description: str,
) -> MaintenanceRequest:

    result = await db.execute(
        select(Machine).where(Machine.id == machine_id)
    )

    machine = result.scalar_one_or_none()

    if machine is None:
        raise ValueError("Machine not found.")

    if not machine.is_active:
        raise ValueError("Machine is inactive.")

    maintenance_request = MaintenanceRequest(
        machine_id=machine_id,
        requested_by=requested_by.id,
        assigned_to=None,
        request_type=request_type,
        priority=priority,
        problem_description=problem_description,
        status="PENDING",
    )

    db.add(maintenance_request)

    await db.flush()

    db.add(
        AuditLog(
            user_id=requested_by.id,
            action="CREATE",
            entity_type="MaintenanceRequest",
            entity_id=maintenance_request.id,
            description="Maintenance request created.",
            old_values=None,
            new_values={
                "machine_id": machine_id,
                "request_type": request_type,
                "priority": priority,
                "status": "PENDING",
            },
        )
    )

    # Notify all active biomedical engineers that
    # a new maintenance request is available.
    engineers = await get_active_engineers(db)

    for engineer in engineers:
        await create_notification(
            db=db,
            user_id=engineer.id,
            title="New Maintenance Request",
            message=(
                f"Maintenance request #{maintenance_request.id} "
                "is available in the shared queue."
            ),
            notification_type=(
                NotificationType.MAINTENANCE_NEW_REQUEST
            ),
            entity_type="MaintenanceRequest",
            entity_id=maintenance_request.id,
            action_required=True,
        )

    await db.commit()
    await db.refresh(maintenance_request)

    return maintenance_request


async def take_maintenance_request(
    db: AsyncSession,
    request_id: int,
    engineer: User,
) -> MaintenanceRequest:

    request = await get_maintenance_request_by_id(
        db,
        request_id,
    )

    if request is None:
        raise ValueError("Maintenance request not found.")

    if request.status != "PENDING":
        raise ValueError("Only pending requests can be taken.")

    if request.assigned_to is not None:
        raise ValueError(
            "Maintenance request is already assigned."
        )

    request.assigned_to = engineer.id

    db.add(
        AuditLog(
            user_id=engineer.id,
            action="TAKE",
            entity_type="MaintenanceRequest",
            entity_id=request.id,
            description="Maintenance request taken by engineer.",
            old_values={
                "assigned_to": None,
                "status": "PENDING",
            },
            new_values={
                "assigned_to": engineer.id,
                "status": "PENDING",
            },
        )
    )

    await db.commit()
    await db.refresh(request)

    return request


async def start_maintenance_request(
    db: AsyncSession,
    request_id: int,
    engineer: User,
) -> MaintenanceRequest:

    request = await get_maintenance_request_by_id(
        db,
        request_id,
    )

    if request is None:
        raise ValueError("Maintenance request not found.")

    if request.assigned_to != engineer.id:
        raise ValueError(
            "Only the assigned engineer can start this request."
        )

    if request.status != "PENDING":
        raise ValueError(
            "Only pending requests can be started."
        )

    request.status = "IN_PROGRESS"

    db.add(
        AuditLog(
            user_id=engineer.id,
            action="START",
            entity_type="MaintenanceRequest",
            entity_id=request.id,
            description="Maintenance request started.",
            old_values={
                "status": "PENDING",
            },
            new_values={
                "status": "IN_PROGRESS",
            },
        )
    )

    await db.commit()
    await db.refresh(request)

    return request


async def release_maintenance_request(
    db: AsyncSession,
    request_id: int,
    engineer: User,
) -> MaintenanceRequest:

    request = await get_maintenance_request_by_id(
        db,
        request_id,
    )

    if request is None:
        raise ValueError("Maintenance request not found.")

    if request.assigned_to is None:
        raise ValueError(
            "Maintenance request is not assigned."
        )

    if request.status not in {
        "PENDING",
        "IN_PROGRESS",
    }:
        raise ValueError(
            "Only pending or in-progress requests can be released."
        )

    # Load the current user's role explicitly to avoid
    # asynchronous lazy-loading issues.
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.id == engineer.id)
    )

    current_engineer = result.scalar_one()

    assigned_engineer_id = request.assigned_to

    # Normal engineers can release only their own tasks.
    # Senior engineers can release another engineer's task.
    if assigned_engineer_id != engineer.id:
        if (
            current_engineer.role is None
            or current_engineer.role.name
            != "Senior Biomedical Engineer"
        ):
            raise ValueError(
                "Only the assigned engineer or a senior "
                "biomedical engineer can release this request."
            )

    old_status = request.status

    request.assigned_to = None
    request.status = "PENDING"

    db.add(
        AuditLog(
            user_id=engineer.id,
            action="RELEASE",
            entity_type="MaintenanceRequest",
            entity_id=request.id,
            description=(
                "Maintenance request released back to "
                "the shared queue."
            ),
            old_values={
                "assigned_to": assigned_engineer_id,
                "status": old_status,
            },
            new_values={
                "assigned_to": None,
                "status": "PENDING",
            },
        )
    )

    # If a senior engineer released someone else's task,
    # notify the engineer whose assignment was removed.
    if assigned_engineer_id != engineer.id:
        await create_notification(
            db=db,
            user_id=assigned_engineer_id,
            title="Maintenance Task Released",
            message=(
                f"Maintenance request #{request.id} "
                "was released from your assignment by "
                "a Senior Biomedical Engineer."
            ),
            notification_type=(
                NotificationType.MAINTENANCE_RELEASED
            ),
            entity_type="MaintenanceRequest",
            entity_id=request.id,
            action_required=False,
        )

    # The released request is treated as newly available.
    # Notify other active engineers.
    engineers = await get_active_engineers(db)

    for other_engineer in engineers:
        if other_engineer.id == assigned_engineer_id:
            continue

        if other_engineer.id == engineer.id:
            continue

        await create_notification(
            db=db,
            user_id=other_engineer.id,
            title="Maintenance Request Available",
            message=(
                f"Maintenance request #{request.id} "
                "has been released and is available "
                "in the shared queue."
            ),
            notification_type=(
                NotificationType.MAINTENANCE_NEW_REQUEST
            ),
            entity_type="MaintenanceRequest",
            entity_id=request.id,
            action_required=True,
        )

    await db.commit()
    await db.refresh(request)

    return request


async def reassign_maintenance_request(
    db: AsyncSession,
    request_id: int,
    senior_engineer: User,
    new_engineer_id: int,
) -> MaintenanceRequest:

    request = await get_maintenance_request_by_id(
        db,
        request_id,
    )

    if request is None:
        raise ValueError("Maintenance request not found.")

    if request.status != "PENDING":
        raise ValueError(
            "Only pending requests can be reassigned."
        )

    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.id == new_engineer_id)
    )

    new_engineer = result.scalar_one_or_none()

    if new_engineer is None:
        raise ValueError("Engineer not found.")

    if not new_engineer.is_active:
        raise ValueError("Engineer is inactive.")

    if (
        new_engineer.role is None
        or new_engineer.role.name not in ENGINEER_ROLES
    ):
        raise ValueError(
            "User is not a biomedical engineer."
        )

    old_assigned_to = request.assigned_to

    request.assigned_to = new_engineer_id

    db.add(
        AuditLog(
            user_id=senior_engineer.id,
            action="REASSIGN",
            entity_type="MaintenanceRequest",
            entity_id=request.id,
            description=(
                "Maintenance request reassigned by "
                "senior biomedical engineer."
            ),
            old_values={
                "assigned_to": old_assigned_to,
                "status": "PENDING",
            },
            new_values={
                "assigned_to": new_engineer_id,
                "status": "PENDING",
            },
        )
    )

    # Notify the newly assigned engineer.
    await create_notification(
        db=db,
        user_id=new_engineer_id,
        title="Maintenance Task Assigned",
        message=(
            f"Maintenance request #{request.id} "
            "was assigned to you."
        ),
        notification_type=(
            NotificationType.MAINTENANCE_REASSIGNED
        ),
        entity_type="MaintenanceRequest",
        entity_id=request.id,
        action_required=True,
    )

    # Notify the previous engineer if there was one
    # and the task was reassigned to somebody else.
    if (
        old_assigned_to is not None
        and old_assigned_to != new_engineer_id
    ):
        await create_notification(
            db=db,
            user_id=old_assigned_to,
            title="Maintenance Task Reassigned",
            message=(
                f"Maintenance request #{request.id} "
                "was reassigned to another engineer."
            ),
            notification_type=(
                NotificationType.MAINTENANCE_REASSIGNED
            ),
            entity_type="MaintenanceRequest",
            entity_id=request.id,
            action_required=False,
        )

    await db.commit()
    await db.refresh(request)

    return request


async def complete_maintenance_request(
    db: AsyncSession,
    request_id: int,
    engineer: User,
) -> MaintenanceRequest:

    request = await get_maintenance_request_by_id(
        db,
        request_id,
    )

    if request is None:
        raise ValueError("Maintenance request not found.")

    if request.assigned_to != engineer.id:
        raise ValueError(
            "Only the assigned engineer can complete "
            "this request."
        )

    if request.status != "IN_PROGRESS":
        raise ValueError(
            "Only in-progress requests can be completed."
        )

    request.status = "COMPLETED"
    request.completed_at = datetime.utcnow()

    db.add(
        AuditLog(
            user_id=engineer.id,
            action="COMPLETE",
            entity_type="MaintenanceRequest",
            entity_id=request.id,
            description="Maintenance request completed.",
            old_values={
                "status": "IN_PROGRESS",
            },
            new_values={
                "status": "COMPLETED",
            },
        )
    )

    # Notify the person who originally requested the maintenance.
    await create_notification(
        db=db,
        user_id=request.requested_by,
        title="Maintenance Completed",
        message=(
            f"Maintenance request #{request.id} "
            "has been completed."
        ),
        notification_type=(
            NotificationType.MAINTENANCE_COMPLETED
        ),
        entity_type="MaintenanceRequest",
        entity_id=request.id,
        action_required=False,
    )

    await db.commit()
    await db.refresh(request)

    return request