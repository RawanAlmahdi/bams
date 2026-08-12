import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.equipment_category import EquipmentCategory
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
async def test_admin_can_create_equipment_category():
    admin = await create_user(
        "System Administrator",
        "test_category_admin",
    )

    name = f"Test Category {uuid.uuid4().hex[:8]}"
    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/equipment-categories",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "name": name,
                    "description": "Test category",
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["name"] == name
        assert data["description"] == "Test category"
        assert data["is_active"] is True

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(EquipmentCategory).where(
                    EquipmentCategory.name == name
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_biomedical_engineer_can_create_equipment_category():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_category_engineer",
    )

    name = f"Engineer Category {uuid.uuid4().hex[:8]}"
    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/equipment-categories",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "name": name,
                },
            )

        assert response.status_code == 201
        assert response.json()["name"] == name

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(EquipmentCategory).where(
                    EquipmentCategory.name == name
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == engineer.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_list_equipment_categories():
    admin = await create_user(
        "System Administrator",
        "test_category_list_admin",
    )

    name = f"List Category {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        category = EquipmentCategory(
            name=name,
            description="List test",
            is_active=True,
        )
        db.add(category)
        await db.commit()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/equipment-categories",
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
                delete(EquipmentCategory).where(
                    EquipmentCategory.name == name
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_update_equipment_category():
    admin = await create_user(
        "System Administrator",
        "test_category_update_admin",
    )

    old_name = f"Old Category {uuid.uuid4().hex[:8]}"
    new_name = f"Updated Category {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        category = EquipmentCategory(
            name=old_name,
            description="Old description",
            is_active=True,
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)

        category_id = category.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/equipment-categories/{category_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "name": new_name,
                    "description": "Updated description",
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["name"] == new_name
        assert data["description"] == "Updated description"

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(EquipmentCategory).where(
                    EquipmentCategory.id == category_id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_deactivate_equipment_category():
    admin = await create_user(
        "System Administrator",
        "test_category_deactivate_admin",
    )

    name = f"Deactivate Category {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        category = EquipmentCategory(
            name=name,
            is_active=True,
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)

        category_id = category.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/equipment-categories/{category_id}/deactivate",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(EquipmentCategory).where(
                    EquipmentCategory.id == category_id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_duplicate_equipment_category_is_rejected():
    admin = await create_user(
        "System Administrator",
        "test_category_duplicate_admin",
    )

    name = f"Duplicate Category {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        category = EquipmentCategory(
            name=name,
            is_active=True,
        )
        db.add(category)
        await db.commit()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/equipment-categories",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "name": name,
                },
            )

        assert response.status_code == 409
        assert (
            response.json()["detail"]
            == "Equipment category name already exists."
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(EquipmentCategory).where(
                    EquipmentCategory.name == name
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_equipment_categories():
    doctor = await create_user(
        "Doctor",
        "test_category_doctor",
    )

    token = create_access_token(doctor.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/equipment-categories",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "name": f"Unauthorized Category {uuid.uuid4().hex[:8]}",
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