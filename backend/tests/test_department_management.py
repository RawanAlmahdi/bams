import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.department import Department
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
            username=f"test_department_admin_{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("Test123!"),
            full_name="Department Admin",
            role_id=role.id,
            account_status="ACTIVE",
            is_active=True,
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        return admin


async def create_doctor():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Role).where(
                Role.name == "Doctor"
            )
        )
        role = result.scalar_one()

        doctor = User(
            username=f"test_department_doctor_{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("Test123!"),
            full_name="Department Doctor",
            role_id=role.id,
            account_status="ACTIVE",
            is_active=True,
        )

        db.add(doctor)
        await db.commit()
        await db.refresh(doctor)

        return doctor


@pytest.mark.asyncio
async def test_admin_can_create_department():
    admin = await create_admin()
    name = f"Test Department {uuid.uuid4().hex[:8]}"
    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/departments",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={"name": name},
            )

        assert response.status_code == 201

        data = response.json()

        assert data["name"] == name
        assert data["is_active"] is True

        department_id = data["id"]

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Department).where(
                    Department.name == name
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_list_departments():
    admin = await create_admin()
    name = f"Test Department {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        department = Department(
            name=name,
            is_active=True,
        )
        db.add(department)
        await db.commit()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/departments",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert any(
            item["name"] == name
            for item in data
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Department).where(
                    Department.name == name
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_get_department():
    admin = await create_admin()
    name = f"Test Department {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        department = Department(
            name=name,
            is_active=True,
        )
        db.add(department)
        await db.commit()
        await db.refresh(department)

        department_id = department.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                f"/departments/{department_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == department_id
        assert data["name"] == name

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Department).where(
                    Department.id == department_id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_update_department():
    admin = await create_admin()

    old_name = f"Old Department {uuid.uuid4().hex[:8]}"
    new_name = f"Updated Department {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        department = Department(
            name=old_name,
            is_active=True,
        )
        db.add(department)
        await db.commit()
        await db.refresh(department)

        department_id = department.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/departments/{department_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={"name": new_name},
            )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == department_id
        assert data["name"] == new_name

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Department).where(
                    Department.id == department_id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_deactivate_department():
    admin = await create_admin()
    name = f"Test Department {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        department = Department(
            name=name,
            is_active=True,
        )
        db.add(department)
        await db.commit()
        await db.refresh(department)

        department_id = department.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/departments/{department_id}/deactivate",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == department_id
        assert data["is_active"] is False

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Department).where(
                    Department.id == department_id
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_duplicate_department_name_is_rejected():
    admin = await create_admin()
    name = f"Test Department {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        department = Department(
            name=name,
            is_active=True,
        )
        db.add(department)
        await db.commit()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/departments",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={"name": name},
            )

        assert response.status_code == 409
        assert (
            response.json()["detail"]
            == "Department name already exists."
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Department).where(
                    Department.name == name
                )
            )
            await db.execute(
                delete(User).where(
                    User.id == admin.id
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_departments():
    doctor = await create_doctor()
    token = create_access_token(doctor.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/departments",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "name": f"Unauthorized Department {uuid.uuid4().hex[:8]}"
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