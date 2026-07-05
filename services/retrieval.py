import uuid
import structlog
from typing import List, Dict, Any
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from sqlmodel import select
from core.database import AsyncSessionLocal
from core.qdrant import qdrant_client, COLLECTION_NAME
from core.embeddings import generate_embeddings
from models.base import DocumentChunk, Document

logger = structlog.get_logger(__name__)

async def retrieve_context(query: str, user_id: uuid.UUID, top_k: int = 20) -> str:
    """Retrieves top-K child chunks, fetches SQLite parent chunks, and assembles formatted context."""
    # 1. Embed query
    embeddings = await generate_embeddings([query])
    query_vector = embeddings[0]
    
    # 2. Qdrant Search with user_id filter (Security enforced DURING retrieval)
    search_result = await qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        query_filter=Filter(
            must=[FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))]
        )
    )
    
    if not search_result.points:
        return ""
        
    parent_chunk_ids = list({uuid.UUID(hit.payload["parent_chunk_id"]) for hit in search_result.points})
    
    # 3. Database Fetch with Dual-Authorization check
    async with AsyncSessionLocal() as session:
        statement = (
            select(DocumentChunk, Document)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(DocumentChunk.id.in_(parent_chunk_ids))
            .where(Document.user_id == user_id)
        )
        results = await session.execute(statement)
        rows = results.all()
        
    # 4. Context Assembly
    context_blocks = []
    for chunk, doc in rows:
        block = f"--- Document: {doc.filename} | Page: {chunk.page_number} ---\n{chunk.content}\n"
        context_blocks.append(block)
        
    return "\n".join(context_blocks)
