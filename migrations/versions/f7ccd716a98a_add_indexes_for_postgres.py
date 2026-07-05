"""add_indexes_for_postgres

Revision ID: f7ccd716a98a
Revises: 006e31c8ff59
Create Date: 2026-07-04 23:20:30.918255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7ccd716a98a'
down_revision: Union[str, Sequence[str], None] = '006e31c8ff59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(op.f('ix_session_user_id'), 'session', ['user_id'], unique=False)
    op.create_index(op.f('ix_document_user_id'), 'document', ['user_id'], unique=False)
    op.create_index(op.f('ix_document_status'), 'document', ['status'], unique=False)
    op.create_index(op.f('ix_documentchunk_document_id'), 'documentchunk', ['document_id'], unique=False)
    op.create_index(op.f('ix_processingjob_document_id'), 'processingjob', ['document_id'], unique=False)
    op.create_index(op.f('ix_processingjob_status'), 'processingjob', ['status'], unique=False)
    op.create_index(op.f('ix_conversation_user_id'), 'conversation', ['user_id'], unique=False)
    op.create_index(op.f('ix_message_conversation_id'), 'message', ['conversation_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_message_conversation_id'), table_name='message')
    op.drop_index(op.f('ix_conversation_user_id'), table_name='conversation')
    op.drop_index(op.f('ix_processingjob_status'), table_name='processingjob')
    op.drop_index(op.f('ix_processingjob_document_id'), table_name='processingjob')
    op.drop_index(op.f('ix_documentchunk_document_id'), table_name='documentchunk')
    op.drop_index(op.f('ix_document_status'), table_name='document')
    op.drop_index(op.f('ix_document_user_id'), table_name='document')
    op.drop_index(op.f('ix_session_user_id'), table_name='session')
