import openai
from typing import List, Dict
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Set OpenAI API key
openai.api_key = settings.OPENAI_API_KEY

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
        Trả lời ngắn gọn, súc tích, dễ hiểu.
        """
        
        user_message = f"""
        Câu hỏi: {question}
        
        Ngữ cảnh:
        {formatted_context}
        """
        
        # Call OpenAI API
        response = await openai.chat.completions.create(
            model=settings.QA_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"Error getting answer from OpenAI: {str(e)}")
        raise Exception(f"Lỗi khi lấy câu trả lời: {str(e)}")
