import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.building import Building
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
            username="test_building_admin",
            password_hash=hash_password("Test123!"),
            full_name="Building Test Admin",
            role_id=role.id,
            account_status="ACTIVE",
            is_active=True,
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        return admin


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_buildings():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Role).where(
                Role.name == "Doctor"
            )
        )

        role = result.scalar_one()

        doctor = User(
            username="test_building_doctor",
            password_hash=hash_password("Test123!"),
            full_name="Building Test Doctor",
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
                "/buildings",
                headers={
                    "Authorization": f"Bearer {token}"
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
async def test_admin_can_create_building():
    admin = await create_admin()
    token = create_access_token(admin.id)

    building_name = "Test Building Create"

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            response = await client.post(
                "/buildings",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "name": building_name
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["name"] == building_name
        assert data["is_active"] is True

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Building).where(
                    Building.name == building_name
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_list_buildings():
    admin = await create_admin()

    building = Building(
        name="Test Building List",
        is_active=True,
    )

    async with AsyncSessionLocal() as db:
        db.add(building)
        await db.commit()
        await db.refresh(building)

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            response = await client.get(
                "/buildings",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        names = [
            item["name"]
            for item in data
        ]

        assert "Test Building List" in names

    finally:
        async with AsyncSessionLocal() as db:
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
async def test_admin_can_update_building():
    admin = await create_admin()

    building = Building(
        name="Test Building Old",
        is_active=True,
    )

    async with AsyncSessionLocal() as db:
        db.add(building)
        await db.commit()
        await db.refresh(building)

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            response = await client.patch(
                f"/buildings/{building.id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "name": "Test Building New"
                },
            )

        assert response.status_code == 200
        assert response.json()["name"] == "Test Building New"

    finally:
        async with AsyncSessionLocal() as db:
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
async def test_admin_can_deactivate_building():
    admin = await create_admin()

    building = Building(
        name="Test Building Deactivate",
        is_active=True,
    )

    async with AsyncSessionLocal() as db:
        db.add(building)
        await db.commit()
        await db.refresh(building)

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            response = await client.patch(
                f"/buildings/{building.id}/deactivate",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    finally:
        async with AsyncSessionLocal() as db:
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