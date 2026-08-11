from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)

    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id"),
        nullable=False,
    )

    maintenance_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PREVENTIVE",
    )

    frequency_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    frequency_unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    next_due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    last_completed_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
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