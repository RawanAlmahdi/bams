from datetime import datetime

from pydantic import BaseModel


class MaintenanceRequestCreate(BaseModel):
    machine_id: int
    request_type: str
    priority: str = "MEDIUM"
    problem_description: str


class MaintenanceRequestUpdate(BaseModel):
    request_type: str
    priority: str
    problem_description: str


class MaintenanceRequestResponse(BaseModel):
    id: int
    machine_id: int
    requested_by: int
    assigned_to: int | None
    request_type: str
    priority: str
    problem_description: str
    status: str
    requested_at: datetime
    completed_at: datetime | None