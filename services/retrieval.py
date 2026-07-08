import uuid
import structlog
import asyncio
from typing import List, Dict, Any, Tuple
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny
from sqlalchemy import select, func, text
from core.database import AsyncSessionLocal
from core.qdrant import qdrant_client, COLLECTION_NAME, RRF_K
from core.embeddings import generate_query_embedding, EmbeddingFatalError, EmbeddingError
from models.base import DocumentChunk, Document
from services.generation import groq_client

logger = structlog.get_logger(__name__)

MAX_CONTEXT_CHARS = 12000

def reciprocal_rank_fusion(rankings: list[list[uuid.UUID]], k: int = 60) -> dict[uuid.UUID, float]:
    scores: dict[uuid.UUID, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return scores

async def rewrite_query_standalone(query: str, chat_history: list[dict]) -> str:
    """Resolve pronouns/references in `query` using recent chat_history so retrieval
    isn't blind to conversational context. Falls back to the original query on any failure."""
    if not groq_client or not chat_history:
        return query
        
    recent_history = chat_history[-4:]
    prompt = (
        "Given the following conversation history, rewrite the user's latest query to be a "
        "standalone search query that contains all necessary context (e.g. resolving pronouns "
        "to the entities they refer to). Reply ONLY with the rewritten query, nothing else.\n\nHistory:\n"
    )
    for msg in recent_history:
        prompt += f"{msg['role'].upper()}: {msg['content']}\n"
    prompt += f"LATEST QUERY: {query}\nREWRITTEN QUERY:"
    
    try:
        response = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=64
        )
        rewritten = response.choices[0].message.content.strip()
        return rewritten if rewritten else query
    except Exception as e:
        logger.warning(f"Query rewrite failed: {e}")
        return query

async def retrieve_context(
    query: str,
    user_id: uuid.UUID,
    document_ids: List[uuid.UUID] = None,
    chat_history: List[Dict[str, Any]] = None,
    top_k: int = 20,
    score_threshold: float = 0.5,
) -> Tuple[str, List[Dict[str, Any]]]:
    if chat_history is None:
        chat_history = []
        
    rewritten_query = await rewrite_query_standalone(query, chat_history)
    
    try:
        query_vector = await generate_query_embedding(rewritten_query)
    except (EmbeddingFatalError, EmbeddingError) as e:
        logger.error(f"Embedding failed during retrieval: {e}")
        return "", []

    must_conditions = [FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))]
    if document_ids:
        must_conditions.append(
            FieldCondition(key="document_id", match=MatchAny(any=[str(did) for did in document_ids]))
        )

    async def dense_search():
        return await qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
            query_filter=Filter(must=must_conditions),
            score_threshold=score_threshold
        )

    async def lexical_search():
        from core.database import engine
        if engine.name == "sqlite":
            return []
            
        async with AsyncSessionLocal() as session:
            stmt = (
                select(DocumentChunk.id, func.ts_rank(DocumentChunk.content_tsv, func.plainto_tsquery(rewritten_query)).label("lexical_score"))
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(Document.user_id == user_id)
                .where(DocumentChunk.content_tsv.op("@@")(func.plainto_tsquery(rewritten_query)))
            )
            if document_ids:
                stmt = stmt.where(Document.id.in_(document_ids))
            stmt = stmt.order_by(text("lexical_score DESC")).limit(top_k)
            res = await session.execute(stmt)
            return res.all()

    dense_res, lexical_res = await asyncio.gather(dense_search(), lexical_search())

    dense_ranking: list[uuid.UUID] = []
    best_score_by_parent: dict[uuid.UUID, float] = {}
    seen = set()
    for hit in dense_res.points:
        pid = uuid.UUID(hit.payload["parent_chunk_id"])
        if pid not in seen:
            seen.add(pid)
            dense_ranking.append(pid)
        best_score_by_parent[pid] = max(best_score_by_parent.get(pid, 0.0), hit.score)
        
    lexical_ranking = [row.id for row in lexical_res]
    
    fused_scores = reciprocal_rank_fusion([dense_ranking, lexical_ranking], k=RRF_K)
    
    if not fused_scores:
        return "", []
        
    merged_parent_ids = list(fused_scores.keys())
    
    async with AsyncSessionLocal() as session:
        statement = (
            select(DocumentChunk, Document)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(DocumentChunk.id.in_(merged_parent_ids))
            .where(Document.user_id == user_id)
        )
        results = await session.execute(statement)
        rows = results.all()
        
    # Sort fetched rows by RRF score descending
    rows.sort(key=lambda x: fused_scores.get(x[0].id, 0.0), reverse=True)
    
    context_blocks = []
    sources = []
    seen_sources = set()
    current_chars = 0
    included = []
    
    for chunk, doc in rows:
        # Deduplicate/skip near-adjacent chunks to compress context
        if chunk.chunk_index is not None:
            if any(c.document_id == chunk.document_id and c.chunk_index is not None and abs(c.chunk_index - chunk.chunk_index) <= 1 for c in included):
                continue
                
        block = f"--- Document: {doc.filename} | Page: {chunk.page_number} ---\n{chunk.content}\n"
        
        if current_chars + len(block) > MAX_CONTEXT_CHARS:
            continue
            
        context_blocks.append(block)
        current_chars += len(block)
        included.append(chunk)
        
        source_key = (doc.filename, chunk.page_number)
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            sources.append({
                "filename": doc.filename,
                "page_number": chunk.page_number,
                "excerpt": chunk.content[:150] + "..." if len(chunk.content) > 150 else chunk.content
            })
            
    return "\n".join(context_blocks), sources
