from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Database URL
DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# Initialize SQLAlchemy
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# File metadata model
class FileMetadata(Base):
    __tablename__ = "files"
    
    file_id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    file_size = Column(Integer)
    file_type = Column(String)
    vector_id = Column(String)
    file_url = Column(String)
    upload_time = Column(DateTime, default=datetime.utcnow)

def create_tables():
    """Create database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}", exc_info=True)
        raise Exception(f"Lỗi khi tạo bảng database: {str(e)}")

def get_db_session():
    """Get database session for dependency injection"""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
