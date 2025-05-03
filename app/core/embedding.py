import openai
from typing import List
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Set OpenAI API key
openai.api_key = settings.OPENAI_API_KEY

async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using OpenAI's embedding model
    """
    try:
        response = await openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts,
        )
        return [data.embedding for data in response.data]
    
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise Exception(f"Lỗi khi tạo embedding: {str(e)}")

async def get_single_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text
    """
    embeddings = await get_embeddings([text])
    return embeddings[0]
