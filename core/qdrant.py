from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams
from core.config import settings
import os

QDRANT_URL = settings.QDRANT_URL
QDRANT_PATH = os.getenv("QDRANT_PATH", "qdrant_data")

if QDRANT_URL:
    qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=settings.QDRANT_API_KEY)
else:
    qdrant_client = AsyncQdrantClient(path=QDRANT_PATH)
COLLECTION_NAME = "recallai_chunks"

async def init_qdrant():
    """Create collection if it doesn't exist."""
    if not await qdrant_client.collection_exists(COLLECTION_NAME):
        await qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE) # text-embedding-004 is 768d
        )
    
    # Ensure indexes exist (idempotent)
    await qdrant_client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="user_id",
        field_schema="keyword"
    )
    await qdrant_client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="document_id",
        field_schema="keyword"
    )
