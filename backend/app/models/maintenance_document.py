from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MaintenanceDocument(Base):
    __tablename__ = "maintenance_documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    maintenance_record_id: Mapped[int] = mapped_column(
        ForeignKey("maintenance_records.id"),
        nullable=False,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
    )

    document_role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )