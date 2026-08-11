from datetime import date, datetime

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AssetAcquisition(Base):
    __tablename__ = "asset_acquisitions"

    id: Mapped[int] = mapped_column(primary_key=True)

    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id"),
        nullable=False,
    )

    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=True,
    )
    
    rpd_request_id: Mapped[int | None] = mapped_column(
    ForeignKey("rpd_requests.id"),
    nullable=True,)

    acquisition_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    acquisition_method: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    acquisition_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    purchase_price: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    warranty_start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    warranty_end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    rpd_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
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