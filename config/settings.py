"""
Configuration management for Chemical Engineering RAG System
Handles environment variables and application settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # Project paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    BOOKS_DIR = DATA_DIR / "books"
    CHROMA_DIR = DATA_DIR / "chroma_db"
    
    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    
    # ChromaDB Settings
    CHROMA_COLLECTION_NAME = "chemical_engineering_books"
    CHROMA_PERSIST_DIRECTORY = str(CHROMA_DIR)
    
    # Embedding Model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    # Text Chunking Parameters
    CHUNK_SIZE = 1000  # tokens
    CHUNK_OVERLAP = 200  # tokens
    
    # RAG Settings
    TOP_K_RESULTS = 8  # Increased for more comprehensive context
    
    # LLM Parameters
    LLM_MODEL = "gemini-2.5-flash"
    LLM_TEMPERATURE = 0.7  # Balanced: factual yet natural responses
    LLM_MAX_TOKENS = 4096  # Increased for comprehensive answers
    LLM_TOP_P = 0.95
    LLM_TOP_K = 40
    
    # Export Settings
    EXPORT_DIR = BASE_DIR / "exports"
    
    # Logging Settings
    LOG_DIR = BASE_DIR / "logs"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10 MB per log file
    LOG_BACKUP_COUNT = 30  # Keep 30 backup files (30 days with daily rotation)
    ENABLE_PERFORMANCE_LOGGING = True  # Enable execution time logging
    
    @classmethod
    def validate(cls):
        """Validate configuration and create necessary directories"""
        # Create directories if they don't exist
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.BOOKS_DIR.mkdir(exist_ok=True)
        cls.CHROMA_DIR.mkdir(exist_ok=True)
        cls.EXPORT_DIR.mkdir(exist_ok=True)
        cls.LOG_DIR.mkdir(exist_ok=True)
        
        # Validate API key
        if not cls.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment variables. "
                "Please create a .env file with your API key."
            )
        
        return True
    
    @classmethod
    def get_books_count(cls):
        """Get count of PDF books in the books directory"""
        if not cls.BOOKS_DIR.exists():
            return 0
        return len(list(cls.BOOKS_DIR.glob("*.pdf")))


# Create settings instance
settings = Settings()
