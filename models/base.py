import uuid
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import TSVECTOR

def utc_now():
    return datetime.now(timezone.utc)

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True)))
    
    sessions: List["Session"] = Relationship(back_populates="user", cascade_delete=True)
    documents: List["Document"] = Relationship(back_populates="user", cascade_delete=True)
    conversations: List["Conversation"] = Relationship(back_populates="user", cascade_delete=True)

class Session(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    last_active: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True)))
    
    user: User = Relationship(back_populates="sessions")

class Document(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    filename: str
    status: str = Field(default="PENDING", index=True)
    embedding_model_version: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True)))
    
    user: User = Relationship(back_populates="documents")
    chunks: List["DocumentChunk"] = Relationship(back_populates="document", cascade_delete=True)
    jobs: List["ProcessingJob"] = Relationship(back_populates="document", cascade_delete=True)

class DocumentChunk(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="document.id", ondelete="CASCADE", index=True)
    page_number: int = Field(default=1)
    chunk_index: Optional[int] = Field(default=None)
    section_title: Optional[str] = Field(default=None)
    content: str
    content_tsv: Optional[str] = Field(default=None, sa_column=Column(TSVECTOR))
    
    document: Document = Relationship(back_populates="chunks")

class ProcessingJob(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="document.id", ondelete="CASCADE", index=True)
    status: str = Field(default="PENDING", index=True) # PENDING, PROCESSING, COMPLETED, FAILED
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True)))
    
    document: Document = Relationship(back_populates="jobs")

class Conversation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    title: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True)))
    
    user: User = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation", cascade_delete=True)

class Message(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id", ondelete="CASCADE", index=True)
    role: str
    content: str
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True)))
    
    conversation: Conversation = Relationship(back_populates="messages")

class TokenBlocklist(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    jti: str = Field(index=True, unique=True)
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))

"""
# MANUAL MIGRATION REQUIRED FOR HYBRID SEARCH
# Since Alembic / migrations are not being managed here, you must run this SQL manually on your PostgreSQL instance:

ALTER TABLE documentchunk ADD COLUMN content_tsv tsvector;

CREATE INDEX ix_documentchunk_content_tsv ON documentchunk USING GIN(content_tsv);

CREATE OR REPLACE FUNCTION documentchunk_tsvector_trigger() RETURNS trigger AS $$
begin
  new.content_tsv := to_tsvector('english', new.content);
  return new;
end
$$ LANGUAGE plpgsql;

CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
ON documentchunk FOR EACH ROW EXECUTE PROCEDURE documentchunk_tsvector_trigger();

# Update existing rows:
UPDATE documentchunk SET content = content;
"""
