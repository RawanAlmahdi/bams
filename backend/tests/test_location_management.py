import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.building import Building
from app.models.floor import Floor
from app.models.location import Location
from app.models.role import Role
from app.models.user import User


async def create_admin(username: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Role).where(
                Role.name == "System Administrator"
            )
        )

        role = result.scalar_one()

        admin = User(
            username=username,
            password_hash=hash_password("Test123!"),
            full_name="Location Test Admin",
            role_id=role.id,
            account_status="ACTIVE",
            is_active=True,
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        return admin


async def create_building_and_floor():
    async with AsyncSessionLocal() as db:
        building = Building(
            name="Test Location Building",
            is_active=True,
        )

        db.add(building)
        await db.commit()
        await db.refresh(building)

        floor = Floor(
            building_id=building.id,
            floor_label="Test Floor",
            is_active=True,
        )

        db.add(floor)
        await db.commit()
        await db.refresh(floor)

        return building.id, floor.id


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_locations():
    admin = None

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Role).where(
                Role.name == "Doctor"
            )
        )

        role = result.scalar_one()

        doctor = User(
            username="test_location_doctor",
            password_hash=hash_password("Test123!"),
            full_name="Location Test Doctor",
            role_id=role.id,
            account_status="ACTIVE",
            is_active=True,
        )

        db.add(doctor)
        await db.commit()
        await db.refresh(doctor)

        doctor_id = doctor.id

    token = create_access_token(doctor_id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/locations",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 403

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(
                    User.id == doctor_id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_create_location():
    admin = await create_admin(
        "test_location_create_admin"
    )

    building_id, floor_id = await create_building_and_floor()

    location_name = "Test MRI Room"

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/locations",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "floor_id": floor_id,
                    "name": location_name,
                    "location_type": "ROOM",
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["floor_id"] == floor_id
        assert data["name"] == location_name
        assert data["location_type"] == "ROOM"
        assert data["is_active"] is True

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Location).where(
                    Location.floor_id == floor_id
                )
            )

            await db.execute(
                delete(Floor).where(
                    Floor.id == floor_id
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
async def test_location_requires_existing_floor():
    admin = await create_admin(
        "test_location_invalid_floor_admin"
    )

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/locations",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "floor_id": 999999,
                    "name": "Invalid Location",
                    "location_type": "ROOM",
                },
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Floor not found."

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_update_location():
    admin = await create_admin(
        "test_location_update_admin"
    )

    building_id, floor_id = await create_building_and_floor()

    async with AsyncSessionLocal() as db:
        location = Location(
            floor_id=floor_id,
            name="Test Location Old",
            location_type="ROOM",
            is_active=True,
        )

        db.add(location)
        await db.commit()
        await db.refresh(location)

        location_id = location.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/locations/{location_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "floor_id": floor_id,
                    "name": "Test Location New",
                    "location_type": "OFFICE",
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["name"] == "Test Location New"
        assert data["location_type"] == "OFFICE"

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Location).where(
                    Location.id == location_id
                )
            )

            await db.execute(
                delete(Floor).where(
                    Floor.id == floor_id
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
async def test_admin_can_deactivate_location():
    admin = await create_admin(
        "test_location_deactivate_admin"
    )

    building_id, floor_id = await create_building_and_floor()

    async with AsyncSessionLocal() as db:
        location = Location(
            floor_id=floor_id,
            name="Test Location Deactivate",
            location_type="ROOM",
            is_active=True,
        )

        db.add(location)
        await db.commit()
        await db.refresh(location)

        location_id = location.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/locations/{location_id}/deactivate",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Location).where(
                    Location.id == location_id
                )
            )

            await db.execute(
                delete(Floor).where(
                    Floor.id == floor_id
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