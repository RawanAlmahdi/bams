from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class MaintenanceHistoryItem(BaseModel):
    maintenance_record_id: int
    maintenance_request_id: int

    request_type: str
    priority: str

    performed_by: int

    started_at: datetime
    completed_at: datetime

    problem_description: str
    work_description: str

    findings: str | None
    recommendations: str | None
    cost: Decimal | None