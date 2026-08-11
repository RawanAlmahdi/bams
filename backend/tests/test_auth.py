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