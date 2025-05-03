import os
import fitz  # PyMuPDF
import docx
import tiktoken
from typing import List, Dict
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize tokenizer for counting tokens
tokenizer = tiktoken.get_encoding("cl100k_base")

async def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from a PDF file"""
    try:
        with fitz.open(stream=file_content, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    except Exception as e:
        logger.error("Error extracting text from PDF", exc_info=True)
        raise Exception(f"Không thể đọc file PDF: {str(e)}")

async def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from a DOCX file"""
    try:
        import io
        doc = docx.Document(io.BytesIO(file_content))
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logger.error("Error extracting text from DOCX", exc_info=True)
        raise Exception(f"Không thể đọc file Word: {str(e)}")

async def extract_text_from_txt(file_content: bytes) -> str:
    """Extract text from a TXT file"""
    try:
        return file_content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            # Try with different encoding
            return file_content.decode('latin-1')
        except Exception as e:
            logger.error("Error extracting text from TXT", exc_info=True)
            raise Exception(f"Không thể đọc file text: {str(e)}")

async def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Split text into chunks with a specific token size and overlap"""
    tokens = tokenizer.encode(text)
    chunks = []
    
    i = 0
    while i < len(tokens):
        # Get a chunk of tokens
        chunk_end = min(i + chunk_size, len(tokens))
        chunk_tokens = tokens[i:chunk_end]
        
        # Convert tokens back to text
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        
        # Move index with overlap
        i += (chunk_size - overlap)
    
    return chunks

async def process_document(file_content: bytes, filename: str) -> List[Dict[str, str]]:
    """Process a document to extract and chunk text"""
    _, file_ext = os.path.splitext(filename)
    file_ext = file_ext.lower()
    
    # Extract text based on file type
    if file_ext == '.pdf':
        text = await extract_text_from_pdf(file_content)
    elif file_ext == '.docx':
        text = await extract_text_from_docx(file_content)
    elif file_ext == '.txt':
        text = await extract_text_from_txt(file_content)
    else:
        raise Exception(f"Không hỗ trợ định dạng file {file_ext}")
    
    # Chunk the text
    text_chunks = await chunk_text(text)
    
    # Format chunks with metadata
    chunks = []
    for i, chunk in enumerate(text_chunks):
        chunks.append({
            "content": chunk,
            "metadata": {
                "filename": filename,
                "chunk": i,
                "source": filename
            }
        })
    
    return chunks
