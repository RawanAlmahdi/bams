import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.permissions import require_role
from app.auth.security import hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.role import Role
from app.models.user import User


@pytest.mark.asyncio
async def test_protected_endpoint_without_token():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_non_admin_role_is_rejected():
    username = "test_doctor"
    password = "Test123!"

    async with AsyncSessionLocal() as db:
        role_result = await db.execute(
            select(Role).where(Role.name == "Doctor")
        )
        doctor_role = role_result.scalar_one()

        test_user = User(
            username=username,
            password_hash=hash_password(password),
            full_name="Test Doctor",
            role_id=doctor_role.id,
            account_status="ACTIVE",
            is_active=True,
        )

        db.add(test_user)
        await db.commit()
        await db.refresh(test_user)

        try:
            role_checker = require_role("System Administrator")

            with pytest.raises(HTTPException) as exc_info:
                await role_checker(test_user)

            assert exc_info.value.status_code == 403

        finally:
            await db.execute(
                delete(User).where(User.id == test_user.id)
            )
            await db.commit()
            
@pytest.mark.asyncio
async def test_user_registration():
    username = "test_registration_user"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/auth/register",
            json={
                "username": username,
                "password": "Test123!",
                "full_name": "Test Registration User",
                "phone": "12345678",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == username
    assert data["account_status"] == "PENDING"

    # Clean up test user
    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(User).where(User.username == username)
        )
        await db.commit()


@pytest.mark.asyncio
async def test_registration_with_existing_username_is_rejected():
    username = "test_duplicate_user"
    password = "Test123!"

    async with AsyncSessionLocal() as db:
        role_result = await db.execute(
            select(Role).where(Role.name == "Pending User")
        )
        pending_role = role_result.scalar_one()

        test_user = User(
            username=username,
            password_hash=hash_password(password),
            full_name="Existing User",
            role_id=pending_role.id,
            account_status="PENDING",
            is_active=False,
        )

        db.add(test_user)
        await db.commit()

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/auth/register",
                json={
                    "username": username,
                    "password": password,
                    "full_name": "Another User",
                    "phone": "12345678",
                },
            )

        assert response.status_code == 409
        assert response.json()["detail"] == "Username already exists"

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(User.username == username)
            )
            await db.commit()


@pytest.mark.asyncio
async def test_pending_user_cannot_login():
    username = "test_pending_login"
    password = "Test123!"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        registration_response = await client.post(
            "/auth/register",
            json={
                "username": username,
                "password": password,
                "full_name": "Pending Login Test",
                "phone": "12345678",
            },
        )

        assert registration_response.status_code == 201

        login_response = await client.post(
            "/auth/login",
            json={
                "username": username,
                "password": password,
            },
        )

    assert login_response.status_code == 403
    assert login_response.json()["detail"] == "User account is inactive"

    # Clean up test user
    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(User).where(User.username == username)
        )
        await db.commit()