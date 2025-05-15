from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from app.utils.logger import get_logger
from app.core.qa_chain import get_answer
from app.db.vector_store import search_similar_chunks
from app.db.models import get_db_session, FileMetadata
from app.api.routes.documents import get_current_document

router = APIRouter(tags=["Q&A"])
logger = get_logger(__name__)

class QuestionRequest(BaseModel):
    question: str
    max_tokens: Optional[int] = 1000
    similarity_threshold: Optional[float] = 0.5
    top_k: Optional[int] = 3

@router.post("/ask")
async def ask_question(
    request: QuestionRequest = Body(...),
    db_session=Depends(get_db_session)
):
    """Ask a question and get an answer based on the uploaded document"""
    try:
        if not request.question:
            raise HTTPException(status_code=400, detail="Câu hỏi không được để trống")

        # Get the current document
        current_doc = await get_current_document(db_session)
        if not current_doc:
            raise HTTPException(
                status_code=404, 
                detail="Không có tài liệu nào được tải lên. Vui lòng tải lên tài liệu trước khi đặt câu hỏi."
            )

        # Search for similar chunks in the vector DB
        relevant_chunks = await search_similar_chunks(
            request.question, 
            file_id=current_doc.file_id,  # Always use the current document
            similarity_threshold=request.similarity_threshold,
            top_k=request.top_k
        )
        
        if not relevant_chunks:
            return {
                "answer": "Vui lòng liên hệ nhân viên để có thông tin chi tiết. Hotline: 0987654321"
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
