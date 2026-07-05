import os
from google import genai
import asyncio
import structlog
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = structlog.get_logger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY", "dummy")
client = genai.Client(api_key=API_KEY) if API_KEY != "dummy" else genai.Client(api_key="mock_key", http_options={"api_version": "v1alpha"})

class EmbeddingError(Exception):
    pass

class EmbeddingFatalError(Exception):
    pass

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(EmbeddingError)
)
async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    if API_KEY == "dummy" and os.environ.get("ENV") != "testing":
        return [[0.1] * 768 for _ in texts]
        
    try:
        response = await client.aio.models.embed_content(
            model="text-embedding-004",
            contents=texts,
        )
        return [emb.values for emb in response.embeddings]
    except Exception as e:
        error_str = str(e)
        if "400" in error_str:
            logger.error(f"Fatal embedding error (400): {e}")
            raise EmbeddingFatalError(f"Bad Request: {e}")
        elif "429" in error_str or "500" in error_str:
            logger.warning(f"Retriable embedding error: {e}")
            raise EmbeddingError(f"Temporary API Failure: {e}")
        else:
            raise EmbeddingFatalError(f"Unexpected Error: {e}")
