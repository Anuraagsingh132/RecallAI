"""add hybrid search columns to documentchunk

Revision ID: d0e24fb439cd
Revises: 9a6bd7949b5f
Create Date: 2026-07-08 22:37:28.447053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0e24fb439cd'
down_revision: Union[str, Sequence[str], None] = '9a6bd7949b5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('documentchunk')]
    
    if 'chunk_index' not in columns:
        op.add_column('documentchunk', sa.Column('chunk_index', sa.Integer(), nullable=True))
        
    if 'section_title' not in columns:
        op.add_column('documentchunk', sa.Column('section_title', sa.String(), nullable=True))
        
    if 'content_tsv' not in columns:
        if bind.dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import TSVECTOR
            op.add_column('documentchunk', sa.Column('content_tsv', TSVECTOR(), nullable=True))
            
            # Setup GIN index and Trigger for FTS
            op.execute("""
                CREATE INDEX IF NOT EXISTS ix_documentchunk_content_tsv 
                ON documentchunk USING GIN (content_tsv);
            """)
            op.execute("""
                CREATE OR REPLACE FUNCTION documentchunk_tsvector_trigger() RETURNS trigger AS $$
                BEGIN
                  NEW.content_tsv := to_tsvector('english', coalesce(NEW.content, ''));
                  RETURN NEW;
                END
                $$ LANGUAGE plpgsql;
            """)
            op.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_trigger WHERE tgname = 'tsvectorupdate' 
                        AND tgrelid = 'documentchunk'::regclass
                    ) THEN
                        CREATE TRIGGER tsvectorupdate
                        BEFORE INSERT OR UPDATE ON documentchunk
                        FOR EACH ROW EXECUTE FUNCTION documentchunk_tsvector_trigger();
                    END IF;
                END
                $$;
            """)
            
            # Backfill existing records
            op.execute("UPDATE documentchunk SET content_tsv = to_tsvector('english', coalesce(content, '')) WHERE content_tsv IS NULL;")
        else:
            op.add_column('documentchunk', sa.Column('content_tsv', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DROP TRIGGER IF EXISTS tsvectorupdate ON documentchunk;")
        op.execute("DROP FUNCTION IF EXISTS documentchunk_tsvector_trigger();")
        op.execute("DROP INDEX IF EXISTS ix_documentchunk_content_tsv;")
        
    op.drop_column('documentchunk', 'content_tsv')
    op.drop_column('documentchunk', 'section_title')
    op.drop_column('documentchunk', 'chunk_index')

