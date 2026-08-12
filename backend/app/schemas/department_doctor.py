from pydantic import BaseModel


class DepartmentDoctorCreate(BaseModel):
    department_id: int
    doctor_id: int
    is_primary: bool = False


class DepartmentDoctorUpdate(BaseModel):
    is_primary: bool


class DepartmentDoctorResponse(BaseModel):
    id: int
    department_id: int
    doctor_id: int
    is_primary: bool
    is_active: bool