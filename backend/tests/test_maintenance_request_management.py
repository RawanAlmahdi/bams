import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from app.models.machine import Machine
from app.models.maintenance_request import MaintenanceRequest
from app.models.notification import Notification
from app.models.role import Role
from app.models.user import User


async def create_user(
    role_name: str,
    prefix: str,
):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Role).where(
                Role.name == role_name
            )
        )

        role = result.scalar_one()

        user = User(
            username=f"{prefix}_{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("Test123!"),
            full_name=f"Test {role_name}",
            role_id=role.id,
            account_status="ACTIVE",
            is_active=True,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user


async def create_machine():
    async with AsyncSessionLocal() as db:
        machine = Machine(
            serial_number=f"SN-{uuid.uuid4().hex[:10]}",
            asset_tag=f"AT-{uuid.uuid4().hex[:10]}",
            name="Test Machine",
            status="NEW",
            condition="NEW",
            is_active=True,
        )

        db.add(machine)
        await db.commit()
        await db.refresh(machine)

        return machine


async def cleanup(
    user_ids: list[int],
    machine_ids: list[int],
):
    async with AsyncSessionLocal() as db:

        # Notifications reference users, so delete them first.
        if user_ids:
            await db.execute(
                delete(Notification).where(
                    Notification.user_id.in_(user_ids)
                )
            )

        for user_id in user_ids:
            await db.execute(
                delete(AuditLog).where(
                    AuditLog.user_id == user_id
                )
            )

        if machine_ids:
            await db.execute(
                delete(MaintenanceRequest).where(
                    MaintenanceRequest.machine_id.in_(
                        machine_ids
                    )
                )
            )

            await db.execute(
                delete(Machine).where(
                    Machine.id.in_(machine_ids)
                )
            )

        if user_ids:
            await db.execute(
                delete(User).where(
                    User.id.in_(user_ids)
                )
            )

        await db.commit()


# ============================================================
# Basic Maintenance Request Tests
# ============================================================


@pytest.mark.asyncio
async def test_technician_can_create_request():
    technician = await create_user(
        "Technician",
        "test_maintenance_technician",
    )

    machine = await create_machine()

    token = create_access_token(technician.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "priority": "HIGH",
                    "problem_description": "Machine stopped working.",
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["machine_id"] == machine.id
        assert data["requested_by"] == technician.id
        assert data["assigned_to"] is None
        assert data["status"] == "PENDING"

    finally:
        await cleanup(
            [technician.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_doctor_can_create_request():
    doctor = await create_user(
        "Doctor",
        "test_maintenance_doctor",
    )

    machine = await create_machine()

    token = create_access_token(doctor.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

        assert response.status_code == 201

    finally:
        await cleanup(
            [doctor.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_rpd_doctor_can_create_request():
    doctor = await create_user(
        "RPD Doctor",
        "test_maintenance_rpd",
    )

    machine = await create_machine()

    token = create_access_token(doctor.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

        assert response.status_code == 201

    finally:
        await cleanup(
            [doctor.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_nurse_can_create_request():
    nurse = await create_user(
        "Nurse",
        "test_maintenance_nurse",
    )

    machine = await create_machine()

    token = create_access_token(nurse.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

        assert response.status_code == 201

    finally:
        await cleanup(
            [nurse.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_biomedical_engineer_can_take_request():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_maintenance_engineer",
    )

    technician = await create_user(
        "Technician",
        "test_maintenance_requester",
    )

    machine = await create_machine()

    token = create_access_token(engineer.id)
    requester_token = create_access_token(technician.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            create_response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {requester_token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

            request_id = create_response.json()["id"]

            response = await client.patch(
                f"/maintenance-requests/{request_id}/take",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["assigned_to"] == engineer.id
        assert data["status"] == "PENDING"

    finally:
        await cleanup(
            [engineer.id, technician.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_engineer_can_start_request():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_maintenance_start_engineer",
    )

    technician = await create_user(
        "Technician",
        "test_maintenance_start_requester",
    )

    machine = await create_machine()

    requester_token = create_access_token(technician.id)
    engineer_token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            create_response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {requester_token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

            request_id = create_response.json()["id"]

            await client.patch(
                f"/maintenance-requests/{request_id}/take",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

            response = await client.patch(
                f"/maintenance-requests/{request_id}/start",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == "IN_PROGRESS"

    finally:
        await cleanup(
            [engineer.id, technician.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_engineer_can_release_request():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_maintenance_release_engineer",
    )

    technician = await create_user(
        "Technician",
        "test_maintenance_release_requester",
    )

    machine = await create_machine()

    requester_token = create_access_token(technician.id)
    engineer_token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            create_response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {requester_token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

            request_id = create_response.json()["id"]

            await client.patch(
                f"/maintenance-requests/{request_id}/take",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

            response = await client.patch(
                f"/maintenance-requests/{request_id}/release",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["assigned_to"] is None
        assert data["status"] == "PENDING"

    finally:
        await cleanup(
            [engineer.id, technician.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_senior_engineer_can_reassign_request():
    senior = await create_user(
        "Senior Biomedical Engineer",
        "test_maintenance_senior",
    )

    engineer_a = await create_user(
        "Biomedical Engineer",
        "test_maintenance_engineer_a",
    )

    engineer_b = await create_user(
        "Biomedical Engineer",
        "test_maintenance_engineer_b",
    )

    technician = await create_user(
        "Technician",
        "test_maintenance_reassign_requester",
    )

    machine = await create_machine()

    requester_token = create_access_token(technician.id)
    engineer_a_token = create_access_token(engineer_a.id)
    senior_token = create_access_token(senior.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            create_response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {requester_token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

            request_id = create_response.json()["id"]

            await client.patch(
                f"/maintenance-requests/{request_id}/take",
                headers={
                    "Authorization": f"Bearer {engineer_a_token}"
                },
            )

            response = await client.patch(
                f"/maintenance-requests/{request_id}/reassign/{engineer_b.id}",
                headers={
                    "Authorization": f"Bearer {senior_token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["assigned_to"] == engineer_b.id
        assert data["status"] == "PENDING"

    finally:
        await cleanup(
            [
                senior.id,
                engineer_a.id,
                engineer_b.id,
                technician.id,
            ],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_engineer_can_complete_request():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_maintenance_complete_engineer",
    )

    technician = await create_user(
        "Technician",
        "test_maintenance_complete_requester",
    )

    machine = await create_machine()

    requester_token = create_access_token(technician.id)
    engineer_token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            create_response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {requester_token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

            request_id = create_response.json()["id"]

            await client.patch(
                f"/maintenance-requests/{request_id}/take",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

            await client.patch(
                f"/maintenance-requests/{request_id}/start",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

            response = await client.patch(
                f"/maintenance-requests/{request_id}/complete",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "COMPLETED"
        assert data["completed_at"] is not None

    finally:
        await cleanup(
            [engineer.id, technician.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_non_requester_cannot_create_maintenance_request():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_maintenance_forbidden_engineer",
    )

    machine = await create_machine()

    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

        assert response.status_code == 403

    finally:
        await cleanup(
            [engineer.id],
            [machine.id],
        )


# ============================================================
# Notification Tests
# ============================================================


@pytest.mark.asyncio
async def test_new_maintenance_request_notifies_engineers():
    technician = await create_user(
        "Technician",
        "test_notification_new_request_technician",
    )

    engineer = await create_user(
        "Biomedical Engineer",
        "test_notification_new_request_engineer",
    )

    senior = await create_user(
        "Senior Biomedical Engineer",
        "test_notification_new_request_senior",
    )

    machine = await create_machine()

    token = create_access_token(technician.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "priority": "HIGH",
                    "problem_description": "Machine issue.",
                },
            )

        assert response.status_code == 201

        request_id = response.json()["id"]

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Notification).where(
                    Notification.entity_id == request_id,
                    Notification.notification_type
                    == "MAINTENANCE_NEW_REQUEST",
                )
            )

            notifications = result.scalars().all()

        recipient_ids = {
            notification.user_id
            for notification in notifications
        }

        assert engineer.id in recipient_ids
        assert senior.id in recipient_ids

        for notification in notifications:
            assert notification.entity_id == request_id
            assert notification.action_required is True
            assert notification.is_read is False

    finally:
        await cleanup(
            [
                technician.id,
                engineer.id,
                senior.id,
            ],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_engineer_release_notifies_other_engineers():
    engineer_a = await create_user(
        "Biomedical Engineer",
        "test_notification_release_a",
    )

    engineer_b = await create_user(
        "Biomedical Engineer",
        "test_notification_release_b",
    )

    senior = await create_user(
        "Senior Biomedical Engineer",
        "test_notification_release_senior",
    )

    technician = await create_user(
        "Technician",
        "test_notification_release_requester",
    )

    machine = await create_machine()

    requester_token = create_access_token(technician.id)
    engineer_token = create_access_token(engineer_a.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            create_response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {requester_token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

            request_id = create_response.json()["id"]

            await client.patch(
                f"/maintenance-requests/{request_id}/take",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

            # Capture notification IDs that existed before release.
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Notification).where(
                        Notification.entity_id == request_id
                    )
                )

                notifications_before_release = result.scalars().all()

            existing_notification_ids = {
                notification.id
                for notification in notifications_before_release
            }

            response = await client.patch(
                f"/maintenance-requests/{request_id}/release",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

        assert response.status_code == 200

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Notification).where(
                    Notification.entity_id == request_id
                )
            )

            notifications_after_release = result.scalars().all()

        # Only inspect notifications created by the release event.
        new_notifications = [
            notification
            for notification in notifications_after_release
            if notification.id not in existing_notification_ids
        ]

        recipient_ids = {
            notification.user_id
            for notification in new_notifications
            if notification.notification_type
            == "MAINTENANCE_NEW_REQUEST"
        }

        assert engineer_b.id in recipient_ids
        assert senior.id in recipient_ids

        # The engineer who released the request does not
        # receive the new-task broadcast.
        assert engineer_a.id not in recipient_ids

    finally:
        await cleanup(
            [
                engineer_a.id,
                engineer_b.id,
                senior.id,
                technician.id,
            ],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_senior_engineer_can_release_other_engineers_task():
    senior = await create_user(
        "Senior Biomedical Engineer",
        "test_notification_senior_release",
    )

    engineer_a = await create_user(
        "Biomedical Engineer",
        "test_notification_senior_release_a",
    )

    engineer_b = await create_user(
        "Biomedical Engineer",
        "test_notification_senior_release_b",
    )

    technician = await create_user(
        "Technician",
        "test_notification_senior_release_requester",
    )

    machine = await create_machine()

    requester_token = create_access_token(technician.id)
    engineer_token = create_access_token(engineer_a.id)
    senior_token = create_access_token(senior.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            create_response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {requester_token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

            request_id = create_response.json()["id"]

            await client.patch(
                f"/maintenance-requests/{request_id}/take",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

            # Capture notifications before the senior releases it.
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Notification).where(
                        Notification.entity_id == request_id
                    )
                )

                notifications_before_release = result.scalars().all()

            existing_notification_ids = {
                notification.id
                for notification in notifications_before_release
            }

            response = await client.patch(
                f"/maintenance-requests/{request_id}/release",
                headers={
                    "Authorization": f"Bearer {senior_token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["assigned_to"] is None
        assert data["status"] == "PENDING"

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Notification).where(
                    Notification.entity_id == request_id
                )
            )

            notifications_after_release = result.scalars().all()

        new_notifications = [
            notification
            for notification in notifications_after_release
            if notification.id not in existing_notification_ids
        ]

        released_notification = next(
            notification
            for notification in new_notifications
            if notification.user_id == engineer_a.id
            and notification.notification_type
            == "MAINTENANCE_RELEASED"
        )

        assert released_notification.action_required is False

        broadcast_recipient_ids = {
            notification.user_id
            for notification in new_notifications
            if notification.notification_type
            == "MAINTENANCE_NEW_REQUEST"
        }

        assert engineer_b.id in broadcast_recipient_ids
        assert engineer_a.id not in broadcast_recipient_ids
        assert senior.id not in broadcast_recipient_ids

    finally:
        await cleanup(
            [
                senior.id,
                engineer_a.id,
                engineer_b.id,
                technician.id,
            ],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_reassignment_notifies_old_and_new_engineers():
    senior = await create_user(
        "Senior Biomedical Engineer",
        "test_notification_reassign_senior",
    )

    engineer_a = await create_user(
        "Biomedical Engineer",
        "test_notification_reassign_a",
    )

    engineer_b = await create_user(
        "Biomedical Engineer",
        "test_notification_reassign_b",
    )

    technician = await create_user(
        "Technician",
        "test_notification_reassign_requester",
    )

    machine = await create_machine()

    requester_token = create_access_token(technician.id)
    engineer_token = create_access_token(engineer_a.id)
    senior_token = create_access_token(senior.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            create_response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {requester_token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

            request_id = create_response.json()["id"]

            await client.patch(
                f"/maintenance-requests/{request_id}/take",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

            response = await client.patch(
                f"/maintenance-requests/{request_id}/reassign/{engineer_b.id}",
                headers={
                    "Authorization": f"Bearer {senior_token}"
                },
            )

        assert response.status_code == 200
        assert response.json()["assigned_to"] == engineer_b.id

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Notification).where(
                    Notification.entity_id == request_id,
                    Notification.notification_type
                    == "MAINTENANCE_REASSIGNED",
                )
            )

            notifications = result.scalars().all()

        recipient_ids = {
            notification.user_id
            for notification in notifications
        }

        assert engineer_a.id in recipient_ids
        assert engineer_b.id in recipient_ids

        new_engineer_notification = next(
            notification
            for notification in notifications
            if notification.user_id == engineer_b.id
        )

        old_engineer_notification = next(
            notification
            for notification in notifications
            if notification.user_id == engineer_a.id
        )

        assert new_engineer_notification.action_required is True
        assert old_engineer_notification.action_required is False

    finally:
        await cleanup(
            [
                senior.id,
                engineer_a.id,
                engineer_b.id,
                technician.id,
            ],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_completed_request_notifies_requester():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_notification_complete_engineer",
    )

    technician = await create_user(
        "Technician",
        "test_notification_complete_requester",
    )

    machine = await create_machine()

    requester_token = create_access_token(technician.id)
    engineer_token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            create_response = await client.post(
                "/maintenance-requests",
                headers={
                    "Authorization": f"Bearer {requester_token}"
                },
                json={
                    "machine_id": machine.id,
                    "request_type": "CORRECTIVE",
                    "problem_description": "Machine issue.",
                },
            )

            request_id = create_response.json()["id"]

            await client.patch(
                f"/maintenance-requests/{request_id}/take",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

            await client.patch(
                f"/maintenance-requests/{request_id}/start",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

            response = await client.patch(
                f"/maintenance-requests/{request_id}/complete",
                headers={
                    "Authorization": f"Bearer {engineer_token}"
                },
            )

        assert response.status_code == 200

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Notification).where(
                    Notification.user_id == technician.id,
                    Notification.entity_id == request_id,
                    Notification.notification_type
                    == "MAINTENANCE_COMPLETED",
                )
            )

            notification = result.scalar_one()

        assert notification.action_required is False
        assert notification.is_read is False

    finally:
        await cleanup(
            [
                engineer.id,
                technician.id,
            ],
            [machine.id],
        )