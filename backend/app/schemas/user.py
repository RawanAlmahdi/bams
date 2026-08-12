from pydantic import BaseModel


class PendingUserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    phone: str | None
    role: str
    account_status: str


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    phone: str | None
    role: str
    account_status: str
    is_active: bool


class ApproveUserRequest(BaseModel):
    role_id: int