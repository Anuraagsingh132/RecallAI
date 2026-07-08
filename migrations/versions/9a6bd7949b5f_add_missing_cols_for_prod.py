"""add missing cols for prod

Revision ID: 9a6bd7949b5f
Revises: 2538ee7bb2e7
Create Date: 2026-07-08 17:08:42.226048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a6bd7949b5f'
down_revision: Union[str, Sequence[str], None] = '2538ee7bb2e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check conversation.title
    conv_cols = [c['name'] for c in inspector.get_columns('conversation')]
    if 'title' not in conv_cols:
        with op.batch_alter_table('conversation', schema=None) as batch_op:
            batch_op.add_column(sa.Column('title', sa.String(), nullable=True))
            
    # Check document.created_at
    doc_cols = [c['name'] for c in inspector.get_columns('document')]
    if 'created_at' not in doc_cols:
        with op.batch_alter_table('document', schema=None) as batch_op:
            batch_op.add_column(sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    doc_cols = [c['name'] for c in inspector.get_columns('document')]
    if 'created_at' in doc_cols:
        with op.batch_alter_table('document', schema=None) as batch_op:
            batch_op.drop_column('created_at')

    conv_cols = [c['name'] for c in inspector.get_columns('conversation')]
    if 'title' in conv_cols:
        with op.batch_alter_table('conversation', schema=None) as batch_op:
            batch_op.drop_column('title')
