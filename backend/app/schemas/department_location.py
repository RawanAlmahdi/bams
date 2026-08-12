from pydantic import BaseModel


class DepartmentLocationCreate(BaseModel):
    department_id: int
    location_id: int


class DepartmentLocationResponse(BaseModel):
    id: int
    department_id: int
    location_id: int