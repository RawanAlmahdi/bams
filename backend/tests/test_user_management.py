import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.role import Role
from app.models.user import User


async def get_role_id(role_name: str) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Role).where(Role.name == role_name)
        )
        role = result.scalar_one()
        return role.id


async def create_test_user(
    username: str,
    role_name: str,
    account_status: str,
    is_active: bool,
) -> User:
    async with AsyncSessionLocal() as db:
        role_result = await db.execute(
            select(Role).where(Role.name == role_name)
        )
        role = role_result.scalar_one()

        user = User(
            username=username,
            password_hash=hash_password("Test123!"),
            full_name="Test User",
            phone="12345678",
            role_id=role.id,
            account_status=account_status,
            is_active=is_active,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user


@pytest.mark.asyncio
async def test_non_admin_cannot_view_pending_users():
    username = "test_pending_non_admin"

    user = await create_test_user(
        username=username,
        role_name="Doctor",
        account_status="ACTIVE",
        is_active=True,
    )

    token = create_access_token(user.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/users/pending",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 403

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(User.id == user.id)
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_view_pending_users():
    admin_username = "test_admin_pending"
    pending_username = "test_pending_user"

    admin = await create_test_user(
        username=admin_username,
        role_name="System Administrator",
        account_status="ACTIVE",
        is_active=True,
    )

    pending_user = await create_test_user(
        username=pending_username,
        role_name="Pending User",
        account_status="PENDING",
        is_active=False,
    )

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/users/pending",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        usernames = [user["username"] for user in data]

        assert pending_username in usernames

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(
                    User.id.in_([admin.id, pending_user.id])
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_approve_pending_user():
    admin_username = "test_admin_approve"
    pending_username = "test_user_approve"

    admin = await create_test_user(
        username=admin_username,
        role_name="System Administrator",
        account_status="ACTIVE",
        is_active=True,
    )

    pending_user = await create_test_user(
        username=pending_username,
        role_name="Pending User",
        account_status="PENDING",
        is_active=False,
    )

    doctor_role_id = await get_role_id("Doctor")

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/users/{pending_user.id}/approve",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "role_id": doctor_role_id
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["username"] == pending_username
        assert data["role"] == "Doctor"
        assert data["account_status"] == "ACTIVE"
        assert data["is_active"] is True

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(
                    User.id.in_([admin.id, pending_user.id])
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_reject_pending_user():
    admin_username = "test_admin_reject"
    pending_username = "test_user_reject"

    admin = await create_test_user(
        username=admin_username,
        role_name="System Administrator",
        account_status="ACTIVE",
        is_active=True,
    )

    pending_user = await create_test_user(
        username=pending_username,
        role_name="Pending User",
        account_status="PENDING",
        is_active=False,
    )

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/users/{pending_user.id}/reject",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["username"] == pending_username
        assert data["account_status"] == "REJECTED"
        assert data["is_active"] is False

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(
                    User.id.in_([admin.id, pending_user.id])
                )
            )
            await db.commit()


@pytest.mark.asyncio
async def test_approved_user_can_login():
    admin_username = "test_admin_login"
    pending_username = "test_user_login"
    password = "Test123!"

    admin = await create_test_user(
        username=admin_username,
        role_name="System Administrator",
        account_status="ACTIVE",
        is_active=True,
    )

    pending_user = await create_test_user(
        username=pending_username,
        role_name="Pending User",
        account_status="PENDING",
        is_active=False,
    )

    doctor_role_id = await get_role_id("Doctor")

    admin_token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            approval_response = await client.patch(
                f"/users/{pending_user.id}/approve",
                headers={
                    "Authorization": f"Bearer {admin_token}"
                },
                json={
                    "role_id": doctor_role_id
                },
            )

            assert approval_response.status_code == 200

            login_response = await client.post(
                "/auth/login",
                json={
                    "username": pending_username,
                    "password": password,
                },
            )

        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(
                    User.id.in_([admin.id, pending_user.id])
                )
            )
            await db.commit()