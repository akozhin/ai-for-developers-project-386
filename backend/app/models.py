"""ORM-модели."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class EventType(Base):
    """Тип события: вид звонка, который предлагает владелец. Ключ — slug владельца."""

    __tablename__ = "event_types"
    __table_args__ = (CheckConstraint("duration_minutes between 5 and 480", name="duration_range"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500))
    duration_minutes: Mapped[int]


class Booking(Base):
    """Бронирование слота гостем (время в UTC)."""

    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ends_after_starts"),
        # Два бронирования (любых типов) не пересекаются по времени; концы интервалов не включаются.
        ExcludeConstraint(
            (func.tstzrange(text("starts_at"), text("ends_at"), "[)"), "&&"),
            using="gist",
            name="bookings_no_overlap",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_type_id: Mapped[str] = mapped_column(ForeignKey("event_types.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    guest_name: Mapped[str] = mapped_column(String(100))
    guest_email: Mapped[str] = mapped_column(String(254))
    comment: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event_type: Mapped[EventType] = relationship(lazy="joined")
