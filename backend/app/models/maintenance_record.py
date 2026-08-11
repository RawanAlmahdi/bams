from datetime import datetime

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[int] = mapped_column(primary_key=True)

    maintenance_request_id: Mapped[int] = mapped_column(
        ForeignKey("maintenance_requests.id"),
        nullable=False,
    )

    performed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    work_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    findings: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recommendations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cost: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )