import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.department import Department
from app.models.department_doctor import DepartmentDoctor
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


async def create_department():
    async with AsyncSessionLocal() as db:
        department = Department(
            name=f"Test Department {uuid.uuid4().hex[:8]}",
            is_active=True,
        )

        db.add(department)
        await db.commit()
        await db.refresh(department)

        return department


@pytest.mark.asyncio
async def test_admin_can_assign_doctor_to_department():
    admin = await create_user(
        "System Administrator",
        "test_dept_doctor_admin",
    )

    doctor = await create_user(
        "Doctor",
        "test_dept_doctor",
    )

    department = await create_department()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/department-doctors",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "department_id": department.id,
                    "doctor_id": doctor.id,
                    "is_primary": True,
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["department_id"] == department.id
        assert data["doctor_id"] == doctor.id
        assert data["is_primary"] is True
        assert data["is_active"] is True

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(DepartmentDoctor).where(
                    DepartmentDoctor.department_id
                    == department.id
                )
            )

            await db.execute(
                delete(Department).where(
                    Department.id == department.id
                )
            )

            await db.execute(
                delete(User).where(
                    User.id.in_([admin.id, doctor.id])
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_rpd_doctor_can_be_assigned():
    admin = await create_user(
        "System Administrator",
        "test_rpd_admin",
    )

    rpd_doctor = await create_user(
        "RPD Doctor",
        "test_rpd_doctor",
    )

    department = await create_department()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/department-doctors",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "department_id": department.id,
                    "doctor_id": rpd_doctor.id,
                    "is_primary": False,
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["doctor_id"] == rpd_doctor.id

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(DepartmentDoctor).where(
                    DepartmentDoctor.department_id
                    == department.id
                )
            )

            await db.execute(
                delete(Department).where(
                    Department.id == department.id
                )
            )

            await db.execute(
                delete(User).where(
                    User.id.in_(
                        [admin.id, rpd_doctor.id]
                    )
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_duplicate_doctor_department_assignment_is_rejected():
    admin = await create_user(
        "System Administrator",
        "test_duplicate_admin",
    )

    doctor = await create_user(
        "Doctor",
        "test_duplicate_doctor",
    )

    department = await create_department()

    async with AsyncSessionLocal() as db:
        assignment = DepartmentDoctor(
            department_id=department.id,
            doctor_id=doctor.id,
            is_primary=False,
            is_active=True,
        )

        db.add(assignment)
        await db.commit()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/department-doctors",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "department_id": department.id,
                    "doctor_id": doctor.id,
                    "is_primary": False,
                },
            )

        assert response.status_code == 409
        assert (
            response.json()["detail"]
            == "Doctor is already assigned to this department."
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(DepartmentDoctor).where(
                    DepartmentDoctor.department_id
                    == department.id
                )
            )

            await db.execute(
                delete(Department).where(
                    Department.id == department.id
                )
            )

            await db.execute(
                delete(User).where(
                    User.id.in_([admin.id, doctor.id])
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_non_doctor_cannot_be_assigned():
    admin = await create_user(
        "System Administrator",
        "test_invalid_role_admin",
    )

    nurse = await create_user(
        "Nurse",
        "test_invalid_role",
    )

    department = await create_department()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/department-doctors",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "department_id": department.id,
                    "doctor_id": nurse.id,
                    "is_primary": False,
                },
            )

        assert response.status_code == 409
        assert (
            response.json()["detail"]
            == "Selected user is not a Doctor or RPD Doctor."
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Department).where(
                    Department.id == department.id
                )
            )

            await db.execute(
                delete(User).where(
                    User.id.in_([admin.id, nurse.id])
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_only_one_primary_doctor_per_department():
    admin = await create_user(
        "System Administrator",
        "test_primary_admin",
    )

    doctor_one = await create_user(
        "Doctor",
        "test_primary_one",
    )

    doctor_two = await create_user(
        "Doctor",
        "test_primary_two",
    )

    department = await create_department()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            first_response = await client.post(
                "/department-doctors",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "department_id": department.id,
                    "doctor_id": doctor_one.id,
                    "is_primary": True,
                },
            )

            assert first_response.status_code == 201

            second_response = await client.post(
                "/department-doctors",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "department_id": department.id,
                    "doctor_id": doctor_two.id,
                    "is_primary": True,
                },
            )

            assert second_response.status_code == 201

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(DepartmentDoctor).where(
                    DepartmentDoctor.department_id
                    == department.id,
                    DepartmentDoctor.is_active.is_(True),
                )
            )

            assignments = list(result.scalars().all())

            primary_assignments = [
                assignment
                for assignment in assignments
                if assignment.is_primary
            ]

            assert len(primary_assignments) == 1
            assert (
                primary_assignments[0].doctor_id
                == doctor_two.id
            )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(DepartmentDoctor).where(
                    DepartmentDoctor.department_id
                    == department.id
                )
            )

            await db.execute(
                delete(Department).where(
                    Department.id == department.id
                )
            )

            await db.execute(
                delete(User).where(
                    User.id.in_(
                        [
                            admin.id,
                            doctor_one.id,
                            doctor_two.id,
                        ]
                    )
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_update_primary_status():
    admin = await create_user(
        "System Administrator",
        "test_update_primary_admin",
    )

    doctor = await create_user(
        "Doctor",
        "test_update_primary_doctor",
    )

    department = await create_department()

    async with AsyncSessionLocal() as db:
        assignment = DepartmentDoctor(
            department_id=department.id,
            doctor_id=doctor.id,
            is_primary=False,
            is_active=True,
        )

        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        assignment_id = assignment.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/department-doctors/{assignment_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "is_primary": True,
                },
            )

        assert response.status_code == 200
        assert response.json()["is_primary"] is True

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(DepartmentDoctor).where(
                    DepartmentDoctor.department_id
                    == department.id
                )
            )

            await db.execute(
                delete(Department).where(
                    Department.id == department.id
                )
            )

            await db.execute(
                delete(User).where(
                    User.id.in_([admin.id, doctor.id])
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_admin_can_deactivate_assignment():
    admin = await create_user(
        "System Administrator",
        "test_deactivate_admin",
    )

    doctor = await create_user(
        "Doctor",
        "test_deactivate_doctor",
    )

    department = await create_department()

    async with AsyncSessionLocal() as db:
        assignment = DepartmentDoctor(
            department_id=department.id,
            doctor_id=doctor.id,
            is_primary=True,
            is_active=True,
        )

        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        assignment_id = assignment.id

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                f"/department-doctors/{assignment_id}/deactivate",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["is_active"] is False
        assert data["is_primary"] is False

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(DepartmentDoctor).where(
                    DepartmentDoctor.id == assignment_id
                )
            )

            await db.execute(
                delete(Department).where(
                    Department.id == department.id
                )
            )

            await db.execute(
                delete(User).where(
                    User.id.in_([admin.id, doctor.id])
                )
            )

            await db.commit()


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_department_doctors():
    doctor = await create_user(
        "Doctor",
        "test_non_admin_doctor",
    )

    department = await create_department()

    token = create_access_token(doctor.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/department-doctors",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "department_id": department.id,
                    "doctor_id": doctor.id,
                    "is_primary": False,
                },
            )

        assert response.status_code == 403

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Department).where(
                    Department.id == department.id
                )
            )

            await db.execute(
                delete(User).where(
                    User.id == doctor.id
                )
            )

            await db.commit()