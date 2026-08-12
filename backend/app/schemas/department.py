from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    name: str


class DepartmentUpdate(BaseModel):
    name: str


class DepartmentResponse(BaseModel):
    id: int
    name: str
    is_active: bool