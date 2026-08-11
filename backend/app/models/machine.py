from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(primary_key=True)

    serial_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    asset_tag: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    model: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("manufacturers.id"),
        nullable=True,
    )

    equipment_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("equipment_types.id"),
        nullable=True,
    )

    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="NEW",
    )

    condition: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NEW",
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