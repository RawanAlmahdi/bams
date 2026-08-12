import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.equipment_category import EquipmentCategory
from app.models.equipment_type import EquipmentType
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


async def create_category():
    async with AsyncSessionLocal() as db:
        category = EquipmentCategory(
            name=f"Test Category {uuid.uuid4().hex[:8]}",
            description="Test category",
            is_active=True,
        )

        db.add(category)
        await db.commit()
        await db.refresh(category)

        return category


@pytest.mark.asyncio
async def test_admin_can_create_equipment_type():
    admin = await create_user(
        "System Administrator",
        "test_type_admin",
    )

    category = await create_category()

    name = f"Test Type {uuid.uuid4().hex[:8]}"
    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/equipment-types",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "category_id": category.id,
                    "name": name,
                    "description": "Test equipment type",
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["category_id"] == category.id
        assert data["name"] == name
        assert data["is_active"] is True

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(EquipmentType).where(
                    EquipmentType.category_id == category.id
                )
            )
            await db.execute(
                delete(EquipmentCategory).where(
                    EquipmentCategory.id == category.id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_biomedical_engineer_can_create_equipment_type():
    engineer = await create_user(
        "Biomedical Engineer",
        "test_type_engineer",
    )

    category = await create_category()

    name = f"Engineer Type {uuid.uuid4().hex[:8]}"
    token = create_access_token(engineer.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/equipment-types",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "category_id": category.id,
                    "name": name,
                },
            )

        assert response.status_code == 201
        assert response.json()["name"] == name

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(EquipmentType).where(
                    EquipmentType.category_id == category.id
                )
            )
            await db.execute(
                delete(EquipmentCategory).where(
                    EquipmentCategory.id == category.id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == engineer.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_list_equipment_types():
    admin = await create_user(
        "System Administrator",
        "test_type_list_admin",
    )

    category = await create_category()

    name = f"List Type {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        equipment_type = EquipmentType(
            category_id=category.id,
            name=name,
            description="List test",
            is_active=True,
        )

        db.add(equipment_type)
        await db.commit()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/equipment-types",
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
                delete(EquipmentType).where(
                    EquipmentType.category_id == category.id
                )
            )
            await db.execute(
                delete(EquipmentCategory).where(
                    EquipmentCategory.id == category.id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_update_equipment_type():
    admin = await create_user(
        "System Administrator",
        "test_type_update_admin",
    )

    category = await create_category()

    old_name = f"Old Type {uuid.uuid4().hex[:8]}"
    new_name = f"Updated Type {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        equipment_type = EquipmentType(
            category_id=category.id,
            name=old_name,
            description="Old description",
            is_active=True,
        )

        db.add(equipment_type)
        await db.commit()
        await db.refresh(equipment_type)

        equipment_type_id = equipment_type.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/equipment-types/{equipment_type_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "category_id": category.id,
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
                delete(EquipmentType).where(
                    EquipmentType.id == equipment_type_id
                )
            )
            await db.execute(
                delete(EquipmentCategory).where(
                    EquipmentCategory.id == category.id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_deactivate_equipment_type():
    admin = await create_user(
        "System Administrator",
        "test_type_deactivate_admin",
    )

    category = await create_category()

    async with AsyncSessionLocal() as db:
        equipment_type = EquipmentType(
            category_id=category.id,
            name=f"Deactivate Type {uuid.uuid4().hex[:8]}",
            is_active=True,
        )

        db.add(equipment_type)
        await db.commit()
        await db.refresh(equipment_type)

        equipment_type_id = equipment_type.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/equipment-types/{equipment_type_id}/deactivate",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(EquipmentType).where(
                    EquipmentType.id == equipment_type_id
                )
            )
            await db.execute(
                delete(EquipmentCategory).where(
                    EquipmentCategory.id == category.id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_duplicate_equipment_type_in_same_category_is_rejected():
    admin = await create_user(
        "System Administrator",
        "test_type_duplicate_admin",
    )

    category = await create_category()

    name = f"Duplicate Type {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        equipment_type = EquipmentType(
            category_id=category.id,
            name=name,
            is_active=True,
        )

        db.add(equipment_type)
        await db.commit()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/equipment-types",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "category_id": category.id,
                    "name": name,
                },
            )

        assert response.status_code == 409
        assert (
            response.json()["detail"]
            == "Equipment type already exists in this category."
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(EquipmentType).where(
                    EquipmentType.category_id == category.id
                )
            )
            await db.execute(
                delete(EquipmentCategory).where(
                    EquipmentCategory.id == category.id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_equipment_type_requires_existing_category():
    admin = await create_user(
        "System Administrator",
        "test_type_invalid_category_admin",
    )

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/equipment-types",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "category_id": 999999,
                    "name": f"Invalid Type {uuid.uuid4().hex[:8]}",
                },
            )

        assert response.status_code == 404
        assert (
            response.json()["detail"]
            == "Equipment category not found."
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_equipment_types():
    doctor = await create_user(
        "Doctor",
        "test_type_doctor",
    )

    token = create_access_token(doctor.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/equipment-types",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "category_id": 999999,
                    "name": f"Unauthorized Type {uuid.uuid4().hex[:8]}",
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