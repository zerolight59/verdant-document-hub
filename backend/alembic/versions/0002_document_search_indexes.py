"""Align document indexes with the SQLAlchemy models.

Revision ID: 0002_search_indexes
Revises: 0001_postgresql
"""

from alembic import op

revision = "0002_search_indexes"
down_revision = "0001_postgresql"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_document_requirements_search", "document_requirements", ["title", "status"]
    )
    op.create_index("ix_research_documents_search", "research_documents", ["name", "category_id"])


def downgrade() -> None:
    op.drop_index("ix_research_documents_search", table_name="research_documents")
    op.drop_index("ix_document_requirements_search", table_name="document_requirements")
