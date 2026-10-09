"""ORM-модели."""

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EventType(Base):
    """Тип события: вид звонка, который предлагает владелец. Ключ — slug владельца."""

    __tablename__ = "event_types"
    __table_args__ = (CheckConstraint("duration_minutes between 5 and 480", name="duration_range"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500))
    duration_minutes: Mapped[int]
