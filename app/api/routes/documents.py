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

@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db_session=Depends(get_db_session)
):
    """Upload a document, process it and store in the system"""
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
        
        return {
            "message": "Upload thành công",
            "file_id": file_id
        }
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("Error uploading document", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.seek(0)

@router.delete("/{file_id}")
async def delete_document(file_id: str, db_session=Depends(get_db_session)):
    """Delete a document and its embeddings by ID"""
    try:
        # Get file metadata
        file_metadata = db_session.query(FileMetadata).filter_by(file_id=file_id).first()
        if not file_metadata:
            raise HTTPException(status_code=404, detail=f"File với ID {file_id} không tồn tại")
        
        # Delete from Firebase
        await delete_from_firebase(file_id, file_metadata.filename)
        
        # Delete from vector DB
        await delete_document_from_vectordb(file_id)
        
        # Delete metadata from database
        db_session.delete(file_metadata)
        db_session.commit()
        
        return {"message": "Xoá thành công"}
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting document {file_id}", exc_info=True)
        db_session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_documents(db_session=Depends(get_db_session)):
    """List all uploaded documents"""
    try:
        files = db_session.query(FileMetadata).all()
        return {
            "documents": [
                {
                    "file_id": file.file_id,
                    "filename": file.filename,
                    "upload_time": file.upload_time,
                    "file_size": file.file_size,
                    "file_type": file.file_type
                } 
                for file in files
            ]
        }
    except Exception as e:
        logger.error("Error listing documents", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
