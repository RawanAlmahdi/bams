from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.permissions import require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import (
    ApproveUserRequest,
    PendingUserResponse,
    UserResponse,
)
from app.services.user import (
    approve_user,
    get_pending_users,
    get_user_by_id,
    reject_user,
)

router = APIRouter(
    prefix="/users",
    tags=["User Management"],
)


@router.get(
    "/pending",
    response_model=list[PendingUserResponse],
)
async def list_pending_users(
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    users = await get_pending_users(db)

    return [
        PendingUserResponse(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            phone=user.phone,
            role=user.role.name,
            account_status=user.account_status,
        )
        for user in users
    ]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user(
    user_id: int,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role.name,
        account_status=user.account_status,
        is_active=user.is_active,
    )


@router.patch(
    "/{user_id}/approve",
    response_model=UserResponse,
)
async def approve_registration(
    user_id: int,
    approval_data: ApproveUserRequest,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await approve_user(
            db=db,
            user_id=user_id,
            role_id=approval_data.role_id,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "User not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role.name,
        account_status=user.account_status,
        is_active=user.is_active,
    )


@router.patch(
    "/{user_id}/reject",
    response_model=UserResponse,
)
async def reject_registration(
    user_id: int,
    current_user: User = Depends(
        require_role("System Administrator")
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await reject_user(
            db=db,
            user_id=user_id,
        )

    except ValueError as exc:
        detail = str(exc)

        if detail == "User not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role.name,
        account_status=user.account_status,
        is_active=user.is_active,
    )