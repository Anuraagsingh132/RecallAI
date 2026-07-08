import uuid
import structlog
from typing import List, Dict, Any, Tuple
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny
from sqlmodel import select
from core.database import AsyncSessionLocal
from core.qdrant import qdrant_client, COLLECTION_NAME
from core.embeddings import generate_embeddings
from models.base import DocumentChunk, Document

logger = structlog.get_logger(__name__)

async def retrieve_context(query: str, user_id: uuid.UUID, document_ids: List[uuid.UUID] = None, top_k: int = 20) -> Tuple[str, List[Dict[str, Any]]]:
    """Retrieves top-K child chunks, fetches SQLite parent chunks, and assembles formatted context."""
    # 1. Embed query
    embeddings = await generate_embeddings([query])
    query_vector = embeddings[0]
    
    # 2. Qdrant Search with user_id filter (Security enforced DURING retrieval)
    must_conditions = [FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))]
    
    if document_ids:
        must_conditions.append(
            FieldCondition(key="document_id", match=MatchAny(any=[str(did) for did in document_ids]))
        )
    
    search_result = await qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        query_filter=Filter(must=must_conditions)
    )
    
    if not search_result.points:
        return "", []
        
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
    sources = []
    for chunk, doc in rows:
        block = f"--- Document: {doc.filename} | Page: {chunk.page_number} ---\n{chunk.content}\n"
        context_blocks.append(block)
        sources.append({
            "filename": doc.filename,
            "page_number": chunk.page_number,
            "excerpt": chunk.content[:150] + "..." if len(chunk.content) > 150 else chunk.content
        })
        
    return "\n".join(context_blocks), sources
