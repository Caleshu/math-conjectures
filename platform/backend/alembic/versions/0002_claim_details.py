"""claims: details, related_claim_ids, reviews

Revision ID: 0002_claim_details
Revises: 0001
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_claim_details"
down_revision = "0001"
branch_labels = None
depends_on = None

J = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    with op.batch_alter_table("claims") as b:
        b.add_column(sa.Column("details", J, nullable=False, server_default="{}"))
        b.add_column(sa.Column("related_claim_ids", J, nullable=False, server_default="[]"))
        b.add_column(sa.Column("reviews", J, nullable=False, server_default="[]"))


def downgrade() -> None:
    with op.batch_alter_table("claims") as b:
        b.drop_column("reviews")
        b.drop_column("related_claim_ids")
        b.drop_column("details")
