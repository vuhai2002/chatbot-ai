import openai
import os
import httpx
from typing import List, Dict
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

async def get_answer(question: str, context_chunks: List[Dict[str, str]], max_tokens: int = 1000) -> str:
    """
    Generate an answer based on the question and relevant text chunks
    
    Args:
        question: User's question
        context_chunks: List of relevant text chunks
        max_tokens: Maximum tokens for the response
        
    Returns:
        Answer text
    """
    try:
        # Format context for the prompt
        formatted_context = "\n\n---\n\n".join([chunk["content"] for chunk in context_chunks])
        
        # Create system and user messages
        system_message = """
        Bạn là trợ lý AI chuyên trả lời câu hỏi dựa trên thông tin từ tài liệu. 
        Hãy trả lời dựa trên ngữ cảnh được cung cấp.
        Nếu câu trả lời không có trong ngữ cảnh, hãy trung thực nói rằng bạn không có thông tin.
        Không được tự tạo ra thông tin hay suy diễn quá xa những gì có trong ngữ cảnh.
        Trả lời đầy đủ thông tin, dễ hiểu.
        """
        
        user_message = f"""
        Câu hỏi: {question}
        
        Ngữ cảnh:
        {formatted_context}
        """
        
        # Call OpenAI API - using client instead of openai global
        # Remove await since client.chat.completions.create is not async
        response = client.chat.completions.create(
            model=settings.QA_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=1.0,
            max_completion_tokens=max_tokens,  # Changed from max_tokens to max_completion_tokens
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"Error getting answer from OpenAI: {str(e)}")
        raise Exception(f"Lỗi khi lấy câu trả lời: {str(e)}")
