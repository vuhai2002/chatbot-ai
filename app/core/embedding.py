import openai
import os
import httpx
from typing import List
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Xóa các biến môi trường proxy nếu có
if 'http_proxy' in os.environ:
    del os.environ['http_proxy']
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']
if 'HTTP_PROXY' in os.environ:
    del os.environ['HTTP_PROXY']
if 'HTTPS_PROXY' in os.environ:
    del os.environ['HTTPS_PROXY']

# Tạo HTTP client không có proxy
http_client = httpx.Client()

# Tạo client OpenAI sử dụng HTTP client tùy chỉnh
client = openai.OpenAI(
    api_key=settings.OPENAI_API_KEY,
    http_client=http_client
)

async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using OpenAI's embedding model
    """
    try:
        # Bỏ từ khóa await vì hàm create() không phải coroutine
        response = client.embeddings.create(
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
