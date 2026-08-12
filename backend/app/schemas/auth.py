#What data is allowed to enter/leave the API?

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    phone: str | None = None


class RegisterResponse(BaseModel):
    message: str
    username: str
    account_status: str