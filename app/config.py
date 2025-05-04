import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Chatbot - Document Q&A"
    PROJECT_DESCRIPTION: str = "API for uploading documents and asking questions"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # OpenAI config
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    QA_MODEL: str = os.getenv("QA_MODEL", "o4-mini")
    
    # Firebase config
    FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS", "")
    FIREBASE_BUCKET: str = os.getenv("FIREBASE_BUCKET", "")
    
    # Vector DB choice (faiss or chroma)
    VECTOR_DB: str = os.getenv("VECTOR_DB", "faiss")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./vectordb")
    
    # PostgreSQL config
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "chatbot_db")
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".docx", ".txt"]
    
    # Logs
    LOG_FOLDER: str = os.getenv("LOG_FOLDER", "logs")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
