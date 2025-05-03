from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from app.utils.logger import get_logger
from app.core.qa_chain import get_answer
from app.db.vector_store import search_similar_chunks
from app.db.models import get_db_session

router = APIRouter(tags=["Q&A"])
logger = get_logger(__name__)

class QuestionRequest(BaseModel):
    question: str
    file_id: Optional[str] = None
    max_tokens: Optional[int] = 1000
    similarity_threshold: Optional[float] = 0.5  # Giảm từ 0.7 xuống 0.5
    top_k: Optional[int] = 3

@router.post("/ask")
async def ask_question(
    request: QuestionRequest = Body(...),
    db_session=Depends(get_db_session)
):
    """Ask a question and get an answer based on the uploaded documents"""
    try:
        if not request.question:
            raise HTTPException(status_code=400, detail="Câu hỏi không được để trống")

        # Search for similar chunks in the vector DB
        relevant_chunks = await search_similar_chunks(
            request.question, 
            file_id=request.file_id,
            similarity_threshold=request.similarity_threshold,
            top_k=request.top_k
        )
        
        if not relevant_chunks:
            return {
                "answer": "Không tìm thấy thông tin liên quan đến câu hỏi của bạn trong tài liệu."
            }
        
        # Get answer using OpenAI
        answer = await get_answer(request.question, relevant_chunks, request.max_tokens)
        
        return {"answer": answer}
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("Error processing question", exc_info=True)
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi khi xử lý câu hỏi")
