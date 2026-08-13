"""Create bounded chat sessions and turns."""

from alembic import op
import sqlalchemy as sa

revision = "0001_chat_continuity"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(32)),
    )
    op.create_table(
        "turns",
        sa.Column(
            "session_id",
            sa.String(32),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sequence", sa.Integer(), primary_key=True),
        sa.Column("role", sa.String(9), primary_key=True),
        sa.Column("text", sa.String(512), nullable=False),
        sa.Column("occurred_at", sa.String(), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_turn_role"),
    )


def downgrade() -> None:
    op.drop_table("turns")
    op.drop_table("sessions")
