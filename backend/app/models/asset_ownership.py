from datetime import date, datetime

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AssetOwnership(Base):
    __tablename__ = "asset_ownerships"

    id: Mapped[int] = mapped_column(primary_key=True)

    machine_id: Mapped[int] = mapped_column(
        ForeignKey("machines.id"),
        nullable=False,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("owners.id"),
        nullable=False,
    )

    ownership_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    ownership_end: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    is_current: Mapped[bool] = mapped_column(
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