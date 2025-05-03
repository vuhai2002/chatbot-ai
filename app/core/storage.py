import os
import json
import firebase_admin
from firebase_admin import credentials, storage
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize Firebase
try:
    # If FIREBASE_CREDENTIALS is a JSON string, parse it
    if settings.FIREBASE_CREDENTIALS and settings.FIREBASE_CREDENTIALS.startswith('{'):
        cred_dict = json.loads(settings.FIREBASE_CREDENTIALS)
        cred = credentials.Certificate(cred_dict)
    # If it's a file path, load it
    elif settings.FIREBASE_CREDENTIALS and os.path.exists(settings.FIREBASE_CREDENTIALS):
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
    else:
        logger.warning("Firebase credentials not provided. Firebase storage won't be available.")
        firebase_app = None

    if 'cred' in locals():
        firebase_app = firebase_admin.initialize_app(cred, {
            'storageBucket': settings.FIREBASE_BUCKET
        })
    
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")
    firebase_app = None

async def upload_to_firebase(file_id: str, file_content: bytes, filename: str) -> str:
    """
    Upload a file to Firebase Storage
    
    Args:
        file_id: Unique ID for the file
        file_content: Binary content of the file
        filename: Original filename
        
    Returns:
        URL of the uploaded file
    """
    if not firebase_app:
        logger.warning("Firebase not initialized. Skipping upload.")
        return "firebase_not_initialized"
    
    try:
        # Get bucket
        bucket = storage.bucket()
        
        # Create a storage reference
        _, ext = os.path.splitext(filename)
        blob_path = f"documents/{file_id}{ext}"
        blob = bucket.blob(blob_path)
        
        # Upload file
        blob.upload_from_string(
            file_content,
            content_type=f"application/{ext[1:]}" if ext[1:] in ['pdf', 'docx'] else 'text/plain'
        )
        
        # Make the file publicly accessible
        blob.make_public()
        
        # Return public URL
        return blob.public_url
    
    except Exception as e:
        logger.error(f"Error uploading to Firebase: {str(e)}", exc_info=True)
        raise Exception(f"Lỗi khi tải lên Firebase: {str(e)}")

async def delete_from_firebase(file_id: str, filename: str) -> bool:
    """
    Delete a file from Firebase Storage
    
    Args:
        file_id: Unique ID of the file
        filename: Original filename
        
    Returns:
        True if successful
    """
    if not firebase_app:
        logger.warning("Firebase not initialized. Skipping deletion.")
        return True
    
    try:
        # Get bucket
        bucket = storage.bucket()
        
        # Create a storage reference
        _, ext = os.path.splitext(filename)
        blob_path = f"documents/{file_id}{ext}"
        blob = bucket.blob(blob_path)
        
        # Delete the blob
        blob.delete()
        
        return True
    
    except Exception as e:
        logger.error(f"Error deleting from Firebase: {str(e)}", exc_info=True)
        raise Exception(f"Lỗi khi xóa từ Firebase: {str(e)}")
