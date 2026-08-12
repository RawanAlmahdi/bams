from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.department_doctor import DepartmentDoctor
from app.models.role import Role
from app.models.user import User


DOCTOR_ROLES = {
    "Doctor",
    "RPD Doctor",
}


async def get_department_doctor_assignments(
    db: AsyncSession,
) -> list[DepartmentDoctor]:
    result = await db.execute(
        select(DepartmentDoctor)
        .where(DepartmentDoctor.is_active.is_(True))
        .order_by(DepartmentDoctor.department_id)
    )

    return list(result.scalars().all())


async def get_department_doctor_by_id(
    db: AsyncSession,
    assignment_id: int,
) -> DepartmentDoctor | None:
    result = await db.execute(
        select(DepartmentDoctor).where(
            DepartmentDoctor.id == assignment_id
        )
    )

    return result.scalar_one_or_none()


async def create_department_doctor_assignment(
    db: AsyncSession,
    department_id: int,
    doctor_id: int,
    is_primary: bool = False,
) -> DepartmentDoctor:

    # Check department
    result = await db.execute(
        select(Department).where(
            Department.id == department_id
        )
    )

    department = result.scalar_one_or_none()

    if department is None:
        raise ValueError("Department not found.")

    if not department.is_active:
        raise ValueError("Department is inactive.")

    # Check doctor and role
    result = await db.execute(
        select(User, Role)
        .join(Role, User.role_id == Role.id)
        .where(User.id == doctor_id)
    )

    doctor_data = result.one_or_none()

    if doctor_data is None:
        raise ValueError("Doctor not found.")

    doctor, role = doctor_data

    if role.name not in DOCTOR_ROLES:
        raise ValueError(
            "Selected user is not a Doctor or RPD Doctor."
        )

    if not doctor.is_active:
        raise ValueError("Doctor account is inactive.")

    # Check existing assignment
    result = await db.execute(
        select(DepartmentDoctor).where(
            DepartmentDoctor.department_id == department_id,
            DepartmentDoctor.doctor_id == doctor_id,
        )
    )

    existing_assignment = result.scalar_one_or_none()

    if existing_assignment is not None:

        if existing_assignment.is_active:
            raise ValueError(
                "Doctor is already assigned to this department."
            )

        # Reactivate an old assignment instead of creating
        # another row because the database has a unique constraint.
        existing_assignment.is_active = True
        existing_assignment.is_primary = is_primary

        if is_primary:
            await db.execute(
                update(DepartmentDoctor)
                .where(
                    DepartmentDoctor.department_id == department_id,
                    DepartmentDoctor.id != existing_assignment.id,
                )
                .values(is_primary=False)
            )

        await db.commit()
        await db.refresh(existing_assignment)

        return existing_assignment

    # Only one primary doctor per department
    if is_primary:
        await db.execute(
            update(DepartmentDoctor)
            .where(
                DepartmentDoctor.department_id == department_id
            )
            .values(is_primary=False)
        )

    assignment = DepartmentDoctor(
        department_id=department_id,
        doctor_id=doctor_id,
        is_primary=is_primary,
        is_active=True,
    )

    db.add(assignment)

    await db.commit()
    await db.refresh(assignment)

    return assignment


async def update_department_doctor_assignment(
    db: AsyncSession,
    assignment_id: int,
    is_primary: bool,
) -> DepartmentDoctor:

    assignment = await get_department_doctor_by_id(
        db,
        assignment_id,
    )

    if assignment is None:
        raise ValueError("Assignment not found.")

    if not assignment.is_active:
        raise ValueError("Assignment is inactive.")

    if is_primary:
        await db.execute(
            update(DepartmentDoctor)
            .where(
                DepartmentDoctor.department_id
                == assignment.department_id,
                DepartmentDoctor.id != assignment.id,
            )
            .values(is_primary=False)
        )

    assignment.is_primary = is_primary

    await db.commit()
    await db.refresh(assignment)

    return assignment


async def deactivate_department_doctor_assignment(
    db: AsyncSession,
    assignment_id: int,
) -> DepartmentDoctor:

    assignment = await get_department_doctor_by_id(
        db,
        assignment_id,
    )

    if assignment is None:
        raise ValueError("Assignment not found.")

    if not assignment.is_active:
        raise ValueError("Assignment is already inactive.")

    assignment.is_active = False
    assignment.is_primary = False

    await db.commit()
    await db.refresh(assignment)

    return assignment