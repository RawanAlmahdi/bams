import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth.security import create_access_token, hash_password
from app.db.database import AsyncSessionLocal
from app.main import app
from app.models.building import Building
from app.models.department import Department
from app.models.department_location import DepartmentLocation
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

        unique_username = f"{username}_{uuid.uuid4().hex[:8]}"

        admin = User(
            username=unique_username,
            password_hash=hash_password("Test123!"),
            full_name="Department Location Admin",
            role_id=role.id,
            account_status="ACTIVE",
            is_active=True,
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        return admin


async def create_test_department_and_location():
    async with AsyncSessionLocal() as db:
        department = Department(
            name=f"Test Radiology Department {uuid.uuid4().hex[:8]}",
            is_active=True,
        )

        db.add(department)
        await db.commit()
        await db.refresh(department)

        building = Building(
            name=f"Test Department Location Building {uuid.uuid4().hex[:8]}",
            is_active=True,
        )

        db.add(building)
        await db.commit()
        await db.refresh(building)

        floor = Floor(
            building_id=building.id,
            floor_label=f"TestFloor{uuid.uuid4().hex[:8]}",
            is_active=True,
        )

        db.add(floor)
        await db.commit()
        await db.refresh(floor)

        location = Location(
            floor_id=floor.id,
            name=f"Test Department Location {uuid.uuid4().hex[:8]}",
            location_type="ROOM",
            is_active=True,
        )

        db.add(location)
        await db.commit()
        await db.refresh(location)

        return (
            department.id,
            location.id,
            floor.id,
            building.id,
        )


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_department_locations():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Role).where(
                Role.name == "Doctor"
            )
        )

        role = result.scalar_one()

        doctor = User(
            username=f"test_department_location_doctor_{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("Test123!"),
            full_name="Department Location Doctor",
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
                "/department-locations",
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
async def test_admin_can_assign_department_to_location():
    admin = await create_admin(
        "test_department_location_admin"
    )

    (
        department_id,
        location_id,
        floor_id,
        building_id,
    ) = await create_test_department_and_location()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/department-locations",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "department_id": department_id,
                    "location_id": location_id,
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["department_id"] == department_id
        assert data["location_id"] == location_id

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(DepartmentLocation).where(
                    DepartmentLocation.department_id
                    == department_id
                )
            )

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
async def test_duplicate_department_location_is_rejected():
    admin = await create_admin(
        "test_department_location_duplicate"
    )

    (
        department_id,
        location_id,
        floor_id,
        building_id,
    ) = await create_test_department_and_location()

    async with AsyncSessionLocal() as db:
        assignment = DepartmentLocation(
            department_id=department_id,
            location_id=location_id,
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
                "/department-locations",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "department_id": department_id,
                    "location_id": location_id,
                },
            )

        assert response.status_code == 409
        assert (
            response.json()["detail"]
            == "Department is already assigned to this location."
        )

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(DepartmentLocation).where(
                    DepartmentLocation.department_id
                    == department_id
                )
            )

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
async def test_department_location_requires_existing_department():
    admin = await create_admin(
        "test_department_location_invalid_department"
    )

    (
        department_id,
        location_id,
        floor_id,
        building_id,
    ) = await create_test_department_and_location()

    token = create_access_token(admin.id)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/department-locations",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "department_id": 999999,
                    "location_id": location_id,
                },
            )

        assert response.status_code == 404
        assert (
            response.json()["detail"]
            == "Department not found."
        )

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
async def test_admin_can_remove_department_location_assignment():
    admin = await create_admin(
        "test_department_location_remove"
    )

    (
        department_id,
        location_id,
        floor_id,
        building_id,
    ) = await create_test_department_and_location()

    async with AsyncSessionLocal() as db:
        assignment = DepartmentLocation(
            department_id=department_id,
            location_id=location_id,
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
            response = await client.delete(
                f"/department-locations/{assignment_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

        assert response.status_code == 204

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(DepartmentLocation).where(
                    DepartmentLocation.id == assignment_id
                )
            )

            assert result.scalar_one_or_none() is None

    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(DepartmentLocation).where(
                    DepartmentLocation.department_id
                    == department_id
                )
            )

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