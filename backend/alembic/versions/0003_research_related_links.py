"""Navigable research references, independent of project links."""

import sqlalchemy as sa

from alembic import op

revision = "0003_research_related_links"
down_revision = "0002_search_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "research_related_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("research_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_id",
            sa.Integer(),
            sa.ForeignKey("research_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "linked_by_id",
            sa.Integer(),
            sa.ForeignKey("employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("source_id", "target_id"),
    )


def downgrade():
    op.drop_table("research_related_links")
