"""bookings_do_not_overlap

Revision ID: da436578dcfc
Revises: 4b45fa8472f8
Create Date: 2026-10-09 19:55:41.364232

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "da436578dcfc"
down_revision: str | Sequence[str] | None = "4b45fa8472f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Два бронирования любых типов не пересекаются по времени (концы интервалов не включаются).

    Autogenerate не видит ограничения EXCLUDE, поэтому миграция написана вручную.
    """
    op.execute(
        "ALTER TABLE bookings ADD CONSTRAINT bookings_no_overlap "
        "EXCLUDE USING gist (tstzrange(starts_at, ends_at, '[)') WITH &&)",
    )


def downgrade() -> None:
    """Убрать ограничение на пересечение."""
    op.drop_constraint("bookings_no_overlap", "bookings", type_="exclude")
