import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.manufacturer import Manufacturer
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


@pytest.mark.asyncio
async def test_admin_can_create_manufacturer():
    admin = await create_user(
        "System Administrator",
        "test_manufacturer_admin",
    )

    name = f"Test Manufacturer {uuid.uuid4().hex[:8]}"
    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/manufacturers",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={"name": name},
            )

        assert response.status_code == 201

        data = response.json()

        assert data["name"] == name
        assert data["is_active"] is True

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Manufacturer).where(
                    Manufacturer.name == name
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_biomedical_engineer_can_create_manufacturer():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_manufacturer_engineer",
    )

    name = f"Engineer Manufacturer {uuid.uuid4().hex[:8]}"
    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/manufacturers",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={"name": name},
            )

        assert response.status_code == 201
        assert response.json()["name"] == name

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Manufacturer).where(
                    Manufacturer.name == name
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == engineer.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_list_manufacturers():
    admin = await create_user(
        "System Administrator",
        "test_manufacturer_list_admin",
    )

    name = f"List Manufacturer {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        manufacturer = Manufacturer(
            name=name,
            is_active=True,
        )

        db.add(manufacturer)
        await db.commit()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/manufacturers",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        assert any(
            item["name"] == name
            for item in response.json()
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Manufacturer).where(
                    Manufacturer.name == name
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_update_manufacturer():
    admin = await create_user(
        "System Administrator",
        "test_manufacturer_update_admin",
    )

    old_name = f"Old Manufacturer {uuid.uuid4().hex[:8]}"
    new_name = f"Updated Manufacturer {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        manufacturer = Manufacturer(
            name=old_name,
            is_active=True,
        )

        db.add(manufacturer)
        await db.commit()
        await db.refresh(manufacturer)

        manufacturer_id = manufacturer.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/manufacturers/{manufacturer_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={"name": new_name},
            )

        assert response.status_code == 200

        assert response.json()["name"] == new_name

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Manufacturer).where(
                    Manufacturer.id == manufacturer_id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_deactivate_manufacturer():
    admin = await create_user(
        "System Administrator",
        "test_manufacturer_deactivate_admin",
    )

    name = f"Deactivate Manufacturer {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        manufacturer = Manufacturer(
            name=name,
            is_active=True,
        )

        db.add(manufacturer)
        await db.commit()
        await db.refresh(manufacturer)

        manufacturer_id = manufacturer.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/manufacturers/{manufacturer_id}/deactivate",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Manufacturer).where(
                    Manufacturer.id == manufacturer_id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_duplicate_manufacturer_is_rejected():
    admin = await create_user(
        "System Administrator",
        "test_manufacturer_duplicate_admin",
    )

    name = f"Duplicate Manufacturer {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        manufacturer = Manufacturer(
            name=name,
            is_active=True,
        )

        db.add(manufacturer)
        await db.commit()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/manufacturers",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={"name": name},
            )

        assert response.status_code == 409
        assert (
            response.json()["detail"]
            == "Manufacturer name already exists."
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Manufacturer).where(
                    Manufacturer.name == name
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_manufacturers():
    doctor = await create_user(
        "Doctor",
        "test_manufacturer_doctor",
    )

    token = create_access_token(doctor.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/manufacturers",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "name": f"Unauthorized Manufacturer {uuid.uuid4().hex[:8]}"
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