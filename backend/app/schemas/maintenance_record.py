from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class MaintenanceRecordCreate(BaseModel):
    work_description: str
    findings: str | None = None
    recommendations: str | None = None
    cost: Decimal | None = None


class MaintenanceRecordUpdate(BaseModel):
    work_description: str
    findings: str | None = None
    recommendations: str | None = None
    cost: Decimal | None = None


class MaintenanceRecordResponse(BaseModel):
    id: int
    maintenance_request_id: int
    performed_by: int
    started_at: datetime
    completed_at: datetime | None
    work_description: str
    findings: str | None
    recommendations: str | None
    cost: Decimal | None