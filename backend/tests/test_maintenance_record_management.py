import uuid
from decimal import Decimal

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
            name="Test Machine",
            status="NEW",
            condition="NEW",
            is_active=True,
        )

        db.add(machine)
        await db.commit()
        await db.refresh(machine)

        return machine


async def create_in_progress_request(
    engineer_id: int,
    machine_id: int,
):
    async with AsyncSessionLocal() as db:
        request = MaintenanceRequest(
            machine_id=machine_id,
            requested_by=engineer_id,
            assigned_to=engineer_id,
            request_type="CORRECTIVE",
            priority="HIGH",
            problem_description="Test maintenance issue.",
            status="IN_PROGRESS",
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
        await db.execute(
            delete(AuditLog).where(
                AuditLog.user_id.in_(user_ids)
            )
        )

        if machine_ids:
            await db.execute(
                delete(MaintenanceRecord).where(
                    MaintenanceRecord.maintenance_request_id.in_(
                        select(MaintenanceRequest.id).where(
                            MaintenanceRequest.machine_id.in_(
                                machine_ids
                            )
                        )
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

        await db.execute(
            delete(User).where(
                User.id.in_(user_ids)
            )
        )

        await db.commit()


@pytest.mark.asyncio
async def test_engineer_can_create_maintenance_record():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_record_create_engineer",
    )

    machine = await create_machine()

    request = await create_in_progress_request(
        engineer.id,
        machine.id,
    )

    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/maintenance-records/request/{request.id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "work_description": "Replaced faulty component.",
                    "findings": "Power component failed.",
                    "recommendations": "Monitor machine.",
                    "cost": "150.00",
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["maintenance_request_id"] == request.id
        assert data["performed_by"] == engineer.id
        assert data["work_description"] == (
            "Replaced faulty component."
        )
        assert data["completed_at"] is None

    finally:
        await cleanup(
            [engineer.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_engineer_can_update_maintenance_record():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_record_update_engineer",
    )

    machine = await create_machine()

    request = await create_in_progress_request(
        engineer.id,
        machine.id,
    )

    async with AsyncSessionLocal() as db:
        record = MaintenanceRecord(
            maintenance_request_id=request.id,
            performed_by=engineer.id,
            work_description="Initial work.",
            findings="Initial finding.",
            started_at=__import__(
                "datetime"
            ).datetime.utcnow(),
        )

        db.add(record)
        await db.commit()
        await db.refresh(record)

        record_id = record.id

    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/maintenance-records/{record_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "work_description": "Updated work.",
                    "findings": "Updated finding.",
                    "recommendations": "Updated recommendation.",
                    "cost": "200.00",
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["work_description"] == "Updated work."
        assert data["findings"] == "Updated finding."
        assert data["recommendations"] == (
            "Updated recommendation."
        )

    finally:
        await cleanup(
            [engineer.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_engineer_can_complete_maintenance_record():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_record_complete_engineer",
    )

    machine = await create_machine()

    request = await create_in_progress_request(
        engineer.id,
        machine.id,
    )

    async with AsyncSessionLocal() as db:
        record = MaintenanceRecord(
            maintenance_request_id=request.id,
            performed_by=engineer.id,
            work_description="Completed maintenance.",
            started_at=__import__(
                "datetime"
            ).datetime.utcnow(),
        )

        db.add(record)
        await db.commit()
        await db.refresh(record)

        record_id = record.id

    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/maintenance-records/{record_id}/complete",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200
        assert response.json()["completed_at"] is not None

    finally:
        await cleanup(
            [engineer.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_non_engineer_cannot_create_maintenance_record():
    doctor = await create_user(
        "Doctor",
        "test_record_doctor",
    )

    machine = await create_machine()

    request = await create_in_progress_request(
        doctor.id,
        machine.id,
    )

    token = create_access_token(doctor.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/maintenance-records/request/{request.id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "work_description": "Unauthorized work.",
                },
            )

        assert response.status_code == 403

    finally:
        await cleanup(
            [doctor.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_only_assigned_engineer_can_create_record():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_record_assigned_engineer",
    )

    other_engineer = await create_user(
        "Biomedical Engineer",
        "test_record_other_engineer",
    )

    machine = await create_machine()

    request = await create_in_progress_request(
        engineer.id,
        machine.id,
    )

    token = create_access_token(other_engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/maintenance-records/request/{request.id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "work_description": "Unauthorized record.",
                },
            )

        assert response.status_code == 404

    finally:
        await cleanup(
            [engineer.id, other_engineer.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_record_requires_in_progress_request():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_record_status_engineer",
    )

    machine = await create_machine()

    async with AsyncSessionLocal() as db:
        request = MaintenanceRequest(
            machine_id=machine.id,
            requested_by=engineer.id,
            assigned_to=engineer.id,
            request_type="CORRECTIVE",
            priority="MEDIUM",
            problem_description="Pending request.",
            status="PENDING",
        )

        db.add(request)
        await db.commit()
        await db.refresh(request)

        request_id = request.id

    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/maintenance-records/request/{request_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "work_description": "Should not work.",
                },
            )

        assert response.status_code == 409

    finally:
        await cleanup(
            [engineer.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_duplicate_record_is_rejected():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_record_duplicate_engineer",
    )

    machine = await create_machine()

    request = await create_in_progress_request(
        engineer.id,
        machine.id,
    )

    async with AsyncSessionLocal() as db:
        record = MaintenanceRecord(
            maintenance_request_id=request.id,
            performed_by=engineer.id,
            work_description="Existing record.",
            started_at=__import__(
                "datetime"
            ).datetime.utcnow(),
        )

        db.add(record)
        await db.commit()

    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/maintenance-records/request/{request.id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "work_description": "Duplicate record.",
                },
            )

        assert response.status_code == 409

    finally:
        await cleanup(
            [engineer.id],
            [machine.id],
        )


@pytest.mark.asyncio
async def test_senior_engineer_can_manage_maintenance_record():
    senior = await create_user(
        "Senior Biomedical Engineer",
        "test_record_senior",
    )

    machine = await create_machine()

    request = await create_in_progress_request(
        senior.id,
        machine.id,
    )

    token = create_access_token(senior.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/maintenance-records/request/{request.id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "work_description": "Senior engineer maintenance.",
                },
            )

        assert response.status_code == 201

    finally:
        await cleanup(
            [senior.id],
            [machine.id],
        )