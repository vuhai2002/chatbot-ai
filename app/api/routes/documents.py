import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from app.config import settings
from app.utils.logger import get_logger
from app.core.document_processor import process_document
from app.core.storage import upload_to_firebase, delete_from_firebase
from app.db.vector_store import add_document_to_vectordb, delete_document_from_vectordb
from app.db.models import FileMetadata, get_db_session

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = get_logger(__name__)

async def get_current_document(db_session):
    """Get the currently stored document, if any"""
    return db_session.query(FileMetadata).first()

@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db_session=Depends(get_db_session)
):
    """Upload a document, replacing any existing document in the system"""
    firebase_delete_message = None
    vectordb_delete_message = None
    
    try:
        # Check file extension
        _, file_ext = os.path.splitext(file.filename)
        if file_ext.lower() not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Không hỗ trợ định dạng file {file_ext}. Định dạng hỗ trợ: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File quá lớn. Kích thước tối đa: {settings.MAX_FILE_SIZE / (1024 * 1024)}MB"
            )
        
        # Delete existing document if any
        existing_doc = await get_current_document(db_session)
        if existing_doc:
            # Try to delete from Firebase - capture result but continue regardless
            try:
                success, message = await delete_from_firebase(existing_doc.file_id, existing_doc.filename)
                if not success:
                    firebase_delete_message = message
                    logger.warning(f"Firebase deletion warning: {message}")
            except Exception as e:
                firebase_delete_message = str(e)
                logger.warning(f"Firebase deletion exception: {str(e)}")
            
            # Try to delete from vector DB - capture result but continue regardless
            try:
                await delete_document_from_vectordb(existing_doc.file_id)
            except Exception as e:
                vectordb_delete_message = str(e)
                logger.warning(f"Vector DB deletion exception: {str(e)}")
            
            # Delete from database
            db_session.delete(existing_doc)
            db_session.commit()
            logger.info(f"Deleted existing document from database: {existing_doc.filename}")
        
        # Create unique ID for the file
        file_id = str(uuid.uuid4())
        
        # Process document to get text chunks
        logger.info(f"Processing document: {file.filename}")
        chunks = await process_document(file_content, file.filename)
        
        # Generate embeddings and add to vector DB
        vector_id = await add_document_to_vectordb(file_id, chunks)
        
        # Upload original file to Firebase
        file_url = await upload_to_firebase(file_id, file_content, file.filename)
        
        # Save metadata to database
        new_file = FileMetadata(
            file_id=file_id,
            filename=file.filename,
            file_size=len(file_content),
            file_type=file_ext.lower(),
            vector_id=vector_id,
            file_url=file_url
        )
        db_session.add(new_file)
        db_session.commit()
        
        response = {
            "message": "Upload thành công. File cũ đã bị thay thế.",
            "file_id": file_id,
            "filename": file.filename
        }
        
        # Add warnings to response if there were any
        if firebase_delete_message:
            response["firebase_warning"] = firebase_delete_message
            
        if vectordb_delete_message:
            response["vectordb_warning"] = vectordb_delete_message
            
        return response
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("Error uploading document", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.seek(0)

@router.get("/current")
async def get_current_document_info(db_session=Depends(get_db_session)):
    """Get information about the currently uploaded document"""
    file = await get_current_document(db_session)
    if not file:
        raise HTTPException(status_code=404, detail="Không có tài liệu nào được tải lên")
    
    return {
        "file_id": file.file_id,
        "filename": file.filename,
        "upload_time": file.upload_time,
        "file_size": file.file_size,
        "file_type": file.file_type
    }

@router.delete("/current")
async def delete_current_document(db_session=Depends(get_db_session)):
    """Delete the currently uploaded document"""
    file = await get_current_document(db_session)
    if not file:
        raise HTTPException(status_code=404, detail="Không có tài liệu nào để xóa")
    
    firebase_message = None
    vectordb_message = None
    
    # Delete from Firebase - capture result but continue regardless
    try:
        success, message = await delete_from_firebase(file.file_id, file.filename)
        if not success:
            firebase_message = message
            logger.warning(f"Firebase deletion warning: {message}")
    except Exception as e:
        firebase_message = str(e)
        logger.warning(f"Firebase deletion exception: {str(e)}")
    
    # Delete from vector DB - capture result but continue regardless
    try:
        await delete_document_from_vectordb(file.file_id)
    except Exception as e:
        vectordb_message = str(e)
        logger.warning(f"Vector DB deletion exception: {str(e)}")
    
    # Always delete metadata from database
    try:
        db_session.delete(file)
        db_session.commit()
        
        response = {"message": "Xoá thành công"}
        if firebase_message:
            response["firebase_warning"] = firebase_message
        if vectordb_message:
            response["vectordb_warning"] = vectordb_message
        
        return response
    except Exception as e:
        logger.error(f"Error deleting document metadata", exc_info=True)
        db_session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
