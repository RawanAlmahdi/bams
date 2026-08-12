import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.building import Building
from app.models.floor import Floor
from app.models.role import Role
from app.models.user import User


async def create_admin():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Role).where(
                Role.name == "System Administrator"
            )
        )

        role = result.scalar_one()

        admin = User(
            username="test_floor_admin",
            password_hash=hash_password("Test123!"),
            full_name="Floor Test Admin",
            role_id=role.id,
            account_status="ACTIVE",
            is_active=True,
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        return admin


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_floors():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Role).where(Role.name == "Doctor")
        )

        role = result.scalar_one()

        doctor = User(
            username="test_floor_doctor",
            password_hash=hash_password("Test123!"),
            full_name="Floor Test Doctor",
            role_id=role.id,
            account_status="ACTIVE",
            is_active=True,
        )

        db.add(doctor)
        await db.commit()
        await db.refresh(doctor)

    token = create_access_token(doctor.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/floors",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 403

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(User.id == doctor.id)
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_create_floor():
    admin = await create_admin()

    async with AsyncSessionLocal() as db:
        building = Building(
            name="Test Floor Building",
            is_active=True,
        )

        db.add(building)
        await db.commit()
        await db.refresh(building)

        building_id = building.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/floors",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "building_id": building_id,
                    "floor_label": "Floor 1",
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["building_id"] == building_id
        assert data["floor_label"] == "Floor 1"
        assert data["is_active"] is True

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Floor).where(
                    Floor.building_id == building_id
                )
            )
            await db.execute(
                delete(Building).where(
                    Building.id == building_id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_floor_requires_existing_building():
    admin = await create_admin()
    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/floors",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "building_id": 999999,
                    "floor_label": "Floor 1",
                },
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Building not found."

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_update_floor():
    admin = await create_admin()

    async with AsyncSessionLocal() as db:
        building = Building(
            name="Test Update Floor Building",
            is_active=True,
        )

        db.add(building)
        await db.commit()
        await db.refresh(building)

        floor = Floor(
            building_id=building.id,
            floor_label="Floor 1",
            is_active=True,
        )

        db.add(floor)
        await db.commit()
        await db.refresh(floor)

        building_id = building.id
        floor_id = floor.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/floors/{floor_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "building_id": building_id,
                    "floor_label": "Floor 2",
                },
            )

        assert response.status_code == 200
        assert response.json()["floor_label"] == "Floor 2"

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Floor).where(Floor.id == floor_id)
            )
            await db.execute(
                delete(Building).where(Building.id == building_id)
            )
            await db.execute(
                delete(User).where(User.id == admin.id)
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_deactivate_floor():
    admin = await create_admin()

    async with AsyncSessionLocal() as db:
        building = Building(
            name="Test Deactivate Floor Building",
            is_active=True,
        )

        db.add(building)
        await db.commit()
        await db.refresh(building)

        floor = Floor(
            building_id=building.id,
            floor_label="Floor 1",
            is_active=True,
        )

        db.add(floor)
        await db.commit()
        await db.refresh(floor)

        building_id = building.id
        floor_id = floor.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/floors/{floor_id}/deactivate",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Floor).where(Floor.id == floor_id)
            )
            await db.execute(
                delete(Building).where(Building.id == building_id)
            )
            await db.execute(
                delete(User).where(User.id == admin.id)
            )
            await db.commit()