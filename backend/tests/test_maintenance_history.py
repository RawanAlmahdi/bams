import uuid
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.audit_log import AuditLog
from app.models.machine import Machine
from app.models.maintenance_record import MaintenanceRecord
from app.models.maintenance_request import MaintenanceRequest
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
            name="History Test Machine",
            status="NEW",
            condition="NEW",
            is_active=True,
        )

        db.add(machine)
        await db.commit()
        await db.refresh(machine)

        return machine


async def create_completed_maintenance(
    engineer_id: int,
    machine_id: int,
    request_type: str = "CORRECTIVE",
    priority: str = "HIGH",
    problem_description: str = "Machine requires maintenance.",
    work_description: str = "Component repaired.",
):
    async with AsyncSessionLocal() as db:
        request = MaintenanceRequest(
            machine_id=machine_id,
            requested_by=engineer_id,
            assigned_to=engineer_id,
            request_type=request_type,
            priority=priority,
            problem_description=problem_description,
            status="COMPLETED",
            completed_at=datetime.utcnow(),
        )

        db.add(request)
        await db.flush()

        record = MaintenanceRecord(
            maintenance_request_id=request.id,
            performed_by=engineer_id,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            work_description=work_description,
            findings="Fault identified and resolved.",
            recommendations="Continue regular maintenance.",
            cost=150.00,
        )

        db.add(record)

        await db.commit()
        await db.refresh(request)
        await db.refresh(record)

        return request, record


async def create_pending_request(
    engineer_id: int,
    machine_id: int,
):
    async with AsyncSessionLocal() as db:
        request = MaintenanceRequest(
            machine_id=machine_id,
            requested_by=engineer_id,
            assigned_to=engineer_id,
            request_type="CORRECTIVE",
            priority="MEDIUM",
            problem_description="Pending maintenance request.",
            status="PENDING",
        )

        db.add(request)
        await db.commit()
        await db.refresh(request)

        return request


async def create_released_request(
    engineer_id: int,
    machine_id: int,
):
    async with AsyncSessionLocal() as db:
        request = MaintenanceRequest(
            machine_id=machine_id,
            requested_by=engineer_id,
            assigned_to=None,
            request_type="CORRECTIVE",
            priority="LOW",
            problem_description="Released maintenance request.",
            status="PENDING",
        )

        db.add(request)
        await db.commit()
        await db.refresh(request)

        return request


async def cleanup(
    user_ids: list[int],
    machine_ids: list[int],
):
    async with AsyncSessionLocal() as db:
        if machine_ids:
            request_ids = select(
                MaintenanceRequest.id
            ).where(
                MaintenanceRequest.machine_id.in_(
                    machine_ids
                )
            )

            await db.execute(
                delete(AuditLog).where(
                    AuditLog.entity_id.in_(request_ids)
                )
            )

            await db.execute(
                delete(MaintenanceRecord).where(
                    MaintenanceRecord.maintenance_request_id.in_(
                        request_ids
                    )
                )
            )

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
                delete(AuditLog).where(
                    AuditLog.user_id.in_(user_ids)
                )
            )

            await db.execute(
                delete(User).where(
                    User.id.in_(user_ids)
                )
            )

        await db.commit()


@pytest.mark.asyncio
async def test_engineer_can_view_machine_maintenance_history():
    engineer = await create_user(
        "Biomedical Engineer",
        "history_engineer",
    )

    machine = await create_machine()

    request, record = await create_completed_maintenance(
        engineer.id,
        machine.id,
    )

    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/machines/{machine.id}/maintenance-history",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1

        item = data[0]

        assert item["maintenance_record_id"] == record.id
        assert item["maintenance_request_id"] == request.id
        assert item["request_type"] == "CORRECTIVE"
        assert item["priority"] == "HIGH"
        assert item["performed_by"] == engineer.id
        assert item["problem_description"] == (
            "Machine requires maintenance."
        )
        assert item["work_description"] == (
            "Component repaired."
        )
        assert item["completed_at"] is not None

    finally:
        await cleanup(
            [engineer.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_senior_engineer_can_view_machine_history():
    senior = await create_user(
        "Senior Biomedical Engineer",
        "history_senior",
    )

    machine = await create_machine()

    await create_completed_maintenance(
        senior.id,
        machine.id,
    )

    token = create_access_token(senior.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/machines/{machine.id}/maintenance-history",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200
        assert len(response.json()) == 1

    finally:
        await cleanup(
            [senior.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_pending_request_does_not_appear_in_history():
    engineer = await create_user(
        "Biomedical Engineer",
        "history_pending",
    )

    machine = await create_machine()

    completed_request, completed_record = (
        await create_completed_maintenance(
            engineer.id,
            machine.id,
        )
    )

    pending_request = await create_pending_request(
        engineer.id,
        machine.id,
    )

    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/machines/{machine.id}/maintenance-history",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1
        assert data[0]["maintenance_record_id"] == (
            completed_record.id
        )
        assert data[0]["maintenance_request_id"] == (
            completed_request.id
        )

        assert all(
            item["maintenance_request_id"]
            != pending_request.id
            for item in data
        )

    finally:
        await cleanup(
            [engineer.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_released_request_does_not_appear_in_history():
    engineer = await create_user(
        "Biomedical Engineer",
        "history_released",
    )

    machine = await create_machine()

    await create_completed_maintenance(
        engineer.id,
        machine.id,
    )

    released_request = await create_released_request(
        engineer.id,
        machine.id,
    )

    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/machines/{machine.id}/maintenance-history",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1

        assert all(
            item["maintenance_request_id"]
            != released_request.id
            for item in data
        )

    finally:
        await cleanup(
            [engineer.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_multiple_completed_records_are_returned():
    engineer = await create_user(
        "Biomedical Engineer",
        "history_multiple",
    )

    machine = await create_machine()

    first_request, first_record = (
        await create_completed_maintenance(
            engineer.id,
            machine.id,
            problem_description="First issue.",
            work_description="First repair.",
        )
    )

    second_request, second_record = (
        await create_completed_maintenance(
            engineer.id,
            machine.id,
            problem_description="Second issue.",
            work_description="Second repair.",
        )
    )

    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/machines/{machine.id}/maintenance-history",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 2

        record_ids = {
            item["maintenance_record_id"]
            for item in data
        }

        assert record_ids == {
            first_record.id,
            second_record.id,
        }

    finally:
        await cleanup(
            [engineer.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_non_engineer_cannot_view_machine_history():
    doctor = await create_user(
        "Doctor",
        "history_doctor",
    )

    machine = await create_machine()

    await create_completed_maintenance(
        doctor.id,
        machine.id,
    )

    token = create_access_token(doctor.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/machines/{machine.id}/maintenance-history",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 403

    finally:
        await cleanup(
            [doctor.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_machine_with_no_completed_maintenance_returns_empty_history():
    engineer = await create_user(
        "Biomedical Engineer",
        "history_empty",
    )

    machine = await create_machine()

    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/machines/{machine.id}/maintenance-history",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200
        assert response.json() == []

    finally:
        await cleanup(
            [engineer.id],
            [machine.id],
        )