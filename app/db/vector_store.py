import os
from typing import List, Dict, Optional
# import faiss
import numpy as np
import chromadb
from chromadb.utils import embedding_functions
import json
import pickle
from app.config import settings
from app.core.embedding import get_embeddings, get_single_embedding
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Ensure vector DB directory exists
os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)

# Choose vector DB based on config
if settings.VECTOR_DB == "chroma":
    # Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=settings.OPENAI_API_KEY,
        model_name=settings.EMBEDDING_MODEL
    )
    
    # Create or get collection
    try:
        collection = chroma_client.get_or_create_collection(
            name="document_chunks",
            embedding_function=openai_ef
        )
    except Exception as e:
        logger.error(f"Error initializing ChromaDB: {str(e)}", exc_info=True)
        raise Exception(f"Lỗi khởi tạo ChromaDB: {str(e)}")
    
else:  # Default to FAISS
    # Initialize FAISS
    faiss_index_path = os.path.join(settings.VECTOR_DB_PATH, "faiss_index.bin")
    metadata_path = os.path.join(settings.VECTOR_DB_PATH, "metadata.pickle")
    
    try:
        if os.path.exists(faiss_index_path):
            # Load existing index
            index = faiss.read_index(faiss_index_path)
            with open(metadata_path, 'rb') as f:
                document_metadata = pickle.load(f)
        else:
            # Create new index
            dimension = 1536  # Dimension for text-embedding-3-small
            index = faiss.IndexFlatL2(dimension)
            document_metadata = {}
    except Exception as e:
        logger.error(f"Error initializing FAISS: {str(e)}", exc_info=True)
        raise Exception(f"Lỗi khởi tạo FAISS: {str(e)}")

async def add_document_to_vectordb(doc_id: str, chunks: List[Dict[str, str]]) -> str:
    """
    Add document chunks to vector database
    
    Args:
        doc_id: Document ID
        chunks: List of text chunks with metadata
        
    Returns:
        Vector store ID
    """
    try:
        # Extract text from chunks
        texts = [chunk["content"] for chunk in chunks]
        
        # Generate embeddings
        embeddings = await get_embeddings(texts)
        
        if settings.VECTOR_DB == "chroma":
            # Add to ChromaDB
            ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
            
            # Thêm doc_id vào metadata
            metadatas = []
            for chunk in chunks:
                # Thêm trường doc_id vào metadata
                metadata = chunk["metadata"].copy()
                metadata["doc_id"] = doc_id
                metadatas.append(metadata)
            
            # Log để debug
            logger.info(f"Adding document to ChromaDB with doc_id: {doc_id}")
            logger.info(f"First metadata example: {metadatas[0] if metadatas else 'No metadata'}")
            
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
        else:  # FAISS
            # Convert embeddings to numpy array
            embeddings_array = np.array(embeddings).astype('float32')
            
            # Get current index size
            current_size = index.ntotal
            
            # Add embeddings to FAISS index
            index.add(embeddings_array)
            
            # Store metadata
            for i, chunk in enumerate(chunks):
                idx = current_size + i
                document_metadata[idx] = {
                    "doc_id": doc_id,
                    "content": chunk["content"],
                    "metadata": chunk["metadata"]
                }
            
            # Save index and metadata
            faiss.write_index(index, faiss_index_path)
            with open(metadata_path, 'wb') as f:
                pickle.dump(document_metadata, f)
        
        return doc_id
    
    except Exception as e:
        logger.error(f"Error adding document to vector DB: {str(e)}", exc_info=True)
        raise Exception(f"Lỗi khi thêm tài liệu vào vector DB: {str(e)}")

async def delete_document_from_vectordb(doc_id: str) -> bool:
    """
    Delete document chunks from vector database
    
    Args:
        doc_id: Document ID
        
    Returns:
        True if successful
    """
    try:
        if settings.VECTOR_DB == "chroma":
            # Delete from ChromaDB
            collection.delete(where={"doc_id": doc_id})
            
        else:  # FAISS
            # FAISS doesn't support direct deletion
            # We need to rebuild the index excluding the document
            global index, document_metadata  # Chỉ khai báo global một lần ở đây
            
            # Filter out document metadata
            new_metadata = {}
            indices_to_keep = []
            
            for idx, data in document_metadata.items():
                if data["doc_id"] != doc_id:
                    new_metadata[len(indices_to_keep)] = data
                    indices_to_keep.append(idx)
            
            if indices_to_keep:
                # Get vectors to keep
                vectors_to_keep = index.reconstruct_batch(np.array(indices_to_keep))
                
                # Create new index
                dimension = vectors_to_keep.shape[1]
                new_index = faiss.IndexFlatL2(dimension)
                new_index.add(vectors_to_keep)
                
                # Replace old index and metadata
                index = new_index
                document_metadata = new_metadata
                
                # Save to disk
                faiss.write_index(index, faiss_index_path)
                with open(metadata_path, 'wb') as f:
                    pickle.dump(document_metadata, f)
            else:
                # If all documents are deleted, create empty index
                dimension = 1536
                index = faiss.IndexFlatL2(dimension)
                document_metadata = {}
                
                # Save to disk
                faiss.write_index(index, faiss_index_path)
                with open(metadata_path, 'wb') as f:
                    pickle.dump(document_metadata, f)
        
        return True
    
    except Exception as e:
        logger.error(f"Error deleting document from vector DB: {str(e)}", exc_info=True)
        raise Exception(f"Lỗi khi xóa tài liệu từ vector DB: {str(e)}")

async def search_similar_chunks(
    query: str, 
    file_id: Optional[str] = None,
    similarity_threshold: float = 0.7,
    top_k: int = 3
) -> List[Dict[str, str]]:
    """
    Search for chunks similar to the query
    
    Args:
        query: Search query
        file_id: Optional file ID to filter results
        similarity_threshold: Minimum similarity score
        top_k: Maximum number of results
        
    Returns:
        List of relevant text chunks
    """
    try:
        # Generate embedding for query
        query_embedding = await get_single_embedding(query)
        
        if settings.VECTOR_DB == "chroma":
            # Search in ChromaDB
            where_filter = {"doc_id": file_id} if file_id else None
            
            # Log query parameters
            logger.info(f"Searching with query: '{query[:30]}...'")
            logger.info(f"Search parameters: file_id={file_id}, threshold={similarity_threshold}, top_k={top_k}")
            logger.info(f"Where filter: {where_filter}")
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter
            )
            
            # Log results
            num_results = len(results['documents'][0]) if results['documents'] else 0
            logger.info(f"Query returned {num_results} raw results")
            
            chunks = []
            for i in range(len(results['documents'][0]) if results['documents'] else 0):
                # Only include if above similarity threshold
                distance = results['distances'][0][i]
                similarity = 1.0 / (1.0 + distance)
                
                logger.info(f"Result {i}: distance={distance}, similarity={similarity}")
                
                if similarity >= similarity_threshold:
                    chunks.append({
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i]
                    })
            
            logger.info(f"Returning {len(chunks)} chunks after threshold filtering")
            
        else:  # FAISS
            # Search in FAISS
            query_embedding_array = np.array([query_embedding]).astype('float32')
            distances, indices = index.search(query_embedding_array, index.ntotal)
            
            # Filter and format results
            chunks = []
            for i, idx in enumerate(indices[0]):
                # Skip if index is invalid
                if idx == -1 or idx >= len(document_metadata):
                    continue
                    
                # Get document data
                doc_data = document_metadata[idx]
                
                # Skip if not from requested file
                if file_id and doc_data["doc_id"] != file_id:
                    continue
                
                # Calculate similarity (convert distance to similarity)
                distance = distances[0][i]
                similarity = 1.0 / (1.0 + distance)
                
                # Only include if above similarity threshold
                if similarity >= similarity_threshold:
                    chunks.append({
                        "content": doc_data["content"],
                        "metadata": doc_data["metadata"]
                    })
                    
                    # Stop if we have enough results
                    if len(chunks) >= top_k:
                        break
        
        return chunks
    
    except Exception as e:
        logger.error(f"Error searching vector DB: {str(e)}", exc_info=True)
        raise Exception(f"Lỗi khi tìm kiếm trong vector DB: {str(e)}")
