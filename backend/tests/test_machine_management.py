import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.building import Building
from app.models.floor import Floor
from app.models.location import Location
from app.models.machine import Machine
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


async def create_location():
    async with AsyncSessionLocal() as db:
        building = Building(
            name=f"Test Machine Building {uuid.uuid4().hex[:8]}",
            is_active=True,
        )

        db.add(building)
        await db.commit()
        await db.refresh(building)

        floor = Floor(
            building_id=building.id,
            floor_label=f"MachFloor{uuid.uuid4().hex[:8]}",
            is_active=True,
        )

        db.add(floor)
        await db.commit()
        await db.refresh(floor)

        location = Location(
            floor_id=floor.id,
            name=f"Machine Location {uuid.uuid4().hex[:8]}",
            location_type="ROOM",
            is_active=True,
        )

        db.add(location)
        await db.commit()
        await db.refresh(location)

        return location, floor, building


@pytest.mark.asyncio
async def test_admin_can_create_machine():
    admin = await create_user(
        "System Administrator",
        "test_machine_admin",
    )

    location, floor, building = await create_location()

    serial = f"SN-{uuid.uuid4().hex[:10]}"
    asset_tag = f"AT-{uuid.uuid4().hex[:8]}"

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/machines",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "serial_number": serial,
                    "asset_tag": asset_tag,
                    "name": "Test Medical Machine",
                    "model": "Model X",
                    "location_id": location.id,
                    "status": "NEW",
                    "condition": "NEW",
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["serial_number"] == serial
        assert data["asset_tag"] == asset_tag
        assert data["name"] == "Test Medical Machine"
        assert data["location_id"] == location.id
        assert data["is_active"] is True

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Machine).where(
                    Machine.serial_number == serial
                )
            )

            await db.execute(
                delete(Location).where(
                    Location.id == location.id
                )
            )

            await db.execute(
                delete(Floor).where(
                    Floor.id == floor.id
                )
            )

            await db.execute(
                delete(Building).where(
                    Building.id == building.id
                )
            )

            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_list_machines():
    admin = await create_user(
        "System Administrator",
        "test_machine_list_admin",
    )

    serial = f"SN-{uuid.uuid4().hex[:10]}"

    async with AsyncSessionLocal() as db:
        machine = Machine(
            serial_number=serial,
            name="Test List Machine",
            status="NEW",
            condition="NEW",
            is_active=True,
        )

        db.add(machine)
        await db.commit()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/machines",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert any(
            item["serial_number"] == serial
            for item in data
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Machine).where(
                    Machine.serial_number == serial
                )
            )

            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_get_machine():
    admin = await create_user(
        "System Administrator",
        "test_machine_get_admin",
    )

    serial = f"SN-{uuid.uuid4().hex[:10]}"

    async with AsyncSessionLocal() as db:
        machine = Machine(
            serial_number=serial,
            name="Test Get Machine",
            status="NEW",
            condition="NEW",
            is_active=True,
        )

        db.add(machine)
        await db.commit()
        await db.refresh(machine)

        machine_id = machine.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/machines/{machine_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == machine_id
        assert data["serial_number"] == serial

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Machine).where(
                    Machine.id == machine_id
                )
            )

            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_update_machine():
    admin = await create_user(
        "System Administrator",
        "test_machine_update_admin",
    )

    serial = f"SN-{uuid.uuid4().hex[:10]}"
    new_asset_tag = f"AT-{uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        machine = Machine(
            serial_number=serial,
            name="Old Machine Name",
            status="NEW",
            condition="NEW",
            is_active=True,
        )

        db.add(machine)
        await db.commit()
        await db.refresh(machine)

        machine_id = machine.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/machines/{machine_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "asset_tag": new_asset_tag,
                    "name": "Updated Machine Name",
                    "model": "Updated Model",
                    "status": "IN_SERVICE",
                    "condition": "GOOD",
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["name"] == "Updated Machine Name"
        assert data["asset_tag"] == new_asset_tag
        assert data["model"] == "Updated Model"
        assert data["status"] == "IN_SERVICE"
        assert data["condition"] == "GOOD"

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Machine).where(
                    Machine.id == machine_id
                )
            )

            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_deactivate_machine():
    admin = await create_user(
        "System Administrator",
        "test_machine_deactivate_admin",
    )

    serial = f"SN-{uuid.uuid4().hex[:10]}"

    async with AsyncSessionLocal() as db:
        machine = Machine(
            serial_number=serial,
            name="Test Deactivate Machine",
            status="NEW",
            condition="NEW",
            is_active=True,
        )

        db.add(machine)
        await db.commit()
        await db.refresh(machine)

        machine_id = machine.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/machines/{machine_id}/deactivate",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Machine).where(
                    Machine.id == machine_id
                )
            )

            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_duplicate_serial_number_is_rejected():
    admin = await create_user(
        "System Administrator",
        "test_machine_duplicate_admin",
    )

    serial = f"SN-{uuid.uuid4().hex[:10]}"

    async with AsyncSessionLocal() as db:
        machine = Machine(
            serial_number=serial,
            name="Existing Machine",
            status="NEW",
            condition="NEW",
            is_active=True,
        )

        db.add(machine)
        await db.commit()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/machines",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "serial_number": serial,
                    "name": "Duplicate Machine",
                    "status": "NEW",
                    "condition": "NEW",
                },
            )

        assert response.status_code == 409
        assert (
            response.json()["detail"]
            == "Serial number already exists."
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Machine).where(
                    Machine.serial_number == serial
                )
            )

            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_machine_requires_existing_location():
    admin = await create_user(
        "System Administrator",
        "test_machine_location_admin",
    )

    serial = f"SN-{uuid.uuid4().hex[:10]}"
    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/machines",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "serial_number": serial,
                    "name": "Invalid Location Machine",
                    "location_id": 999999,
                    "status": "NEW",
                    "condition": "NEW",
                },
            )

        assert response.status_code == 404
        assert (
            response.json()["detail"]
            == "Location not found."
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Machine).where(
                    Machine.serial_number == serial
                )
            )

            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_machines():
    doctor = await create_user(
        "Doctor",
        "test_machine_doctor",
    )

    token = create_access_token(doctor.id)

    serial = f"SN-{uuid.uuid4().hex[:10]}"

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/machines",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "serial_number": serial,
                    "name": "Unauthorized Machine",
                    "status": "NEW",
                    "condition": "NEW",
                },
            )

        assert response.status_code == 403

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(
                    User.id == doctor.id
                )
            )

            await db.commit()
@pytest.mark.asyncio
async def test_biomedical_engineer_can_create_machine():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_machine_engineer",
    )

    serial = f"SN-{uuid.uuid4().hex[:10]}"

    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/machines",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "serial_number": serial,
                    "name": "Engineer Added Machine",
                    "status": "NEW",
                    "condition": "NEW",
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["serial_number"] == serial
        assert data["name"] == "Engineer Added Machine"
        assert data["is_active"] is True

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Machine).where(
                    Machine.serial_number == serial
                )
            )

            await db.execute(
                delete(User).where(
                    User.id == engineer.id
                )
            )

            await db.commit()