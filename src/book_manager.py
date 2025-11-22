"""
Book Manager Module
Tracks which books have been processed and provides smart book management
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime
from config.settings import settings
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class BookManager:
    """Manage book processing tracking and detection of new books"""
    
    def __init__(self, tracker_file: str = None):
        """
        Initialize book manager
        
        Args:
            tracker_file: Path to JSON tracker file (default: data/book_tracker.json)
        """
        self.tracker_file = Path(tracker_file) if tracker_file else settings.DATA_DIR / "book_tracker.json"
        logger.info(f"Initializing BookManager | Tracker file: {self.tracker_file}")
        self.processed_books = self._load_tracker()
        logger.info(f"BookManager initialized | Processed books: {len(self.processed_books)}")
    
    def _load_tracker(self) -> Dict[str, Any]:
        """Load the book tracker from JSON file"""
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    books = data.get('processed_books', {})
                    logger.debug(f"Loaded tracker file | Books: {len(books)}")
                    return books
            except Exception as e:
                logger.error(f"Error loading tracker file: {type(e).__name__}: {str(e)}")
                return {}
        logger.debug("Tracker file does not exist, starting fresh")
        return {}
    
    def _save_tracker(self) -> None:
        """Save the book tracker to JSON file"""
        try:
            self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.tracker_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'processed_books': self.processed_books,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
            logger.debug(f"Tracker file saved | Books: {len(self.processed_books)}")
        except Exception as e:
            logger.error(f"Error saving tracker file: {type(e).__name__}: {str(e)}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate MD5 hash of a file
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash string
        """
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def is_processed(self, file_path: Path) -> bool:
        """
        Check if a book has been processed
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            True if book is already processed and unchanged
        """
        file_name = file_path.name
        
        if file_name not in self.processed_books:
            logger.debug(f"Book not in tracker: {file_name}")
            return False
        
        # Check if file has been modified (compare hash)
        current_hash = self._calculate_file_hash(file_path)
        stored_hash = self.processed_books[file_name].get('file_hash', '')
        
        is_same = current_hash == stored_hash
        if not is_same:
            logger.info(f"Book modified (hash mismatch): {file_name}")
        
        return is_same
    
    def mark_as_processed(self, file_path: Path, chunk_count: int) -> None:
        """
        Mark a book as processed
        
        Args:
            file_path: Path to PDF file
            chunk_count: Number of chunks created
        """
        file_name = file_path.name
        file_hash = self._calculate_file_hash(file_path)
        
        self.processed_books[file_name] = {
            'file_path': str(file_path),
            'file_hash': file_hash,
            'chunk_count': chunk_count,
            'processed_date': datetime.now().isoformat(),
            'file_size': file_path.stat().st_size
        }
        
        self._save_tracker()
        logger.info(f"Marked as processed: {file_name} | Chunks: {chunk_count}")
    
    def get_new_books(self, books_directory: Path = None) -> List[Path]:
        """
        Get list of books that need processing (new or modified)
        
        Args:
            books_directory: Directory containing PDF books (default: settings.BOOKS_DIR)
            
        Returns:
            List of PDF file paths that need processing
        """
        books_dir = books_directory or settings.BOOKS_DIR
        logger.debug(f"Scanning for new books in: {books_dir}")
        
        if not books_dir.exists():
            logger.warning(f"Books directory does not exist: {books_dir}")
            return []
        
        # Get all PDF files
        all_pdfs = list(books_dir.glob("*.pdf"))
        
        # Filter to only new or modified books
        new_books = [
            pdf for pdf in all_pdfs
            if not self.is_processed(pdf)
        ]
        
        logger.info(f"Found {len(new_books)} new/modified books out of {len(all_pdfs)} total")
        return new_books
    
    def get_processed_books(self) -> List[str]:
        """
        Get list of all processed book names
        
        Returns:
            List of processed book filenames
        """
        return list(self.processed_books.keys())
    
    def get_book_info(self, file_name: str) -> Dict[str, Any]:
        """
        Get information about a processed book
        
        Args:
            file_name: Name of the book file
            
        Returns:
            Dictionary with book processing info
        """
        return self.processed_books.get(file_name, {})
    
    def remove_book(self, file_name: str) -> None:
        """
        Remove a book from the tracker (for reprocessing)
        
        Args:
            file_name: Name of the book file
        """
        if file_name in self.processed_books:
            del self.processed_books[file_name]
            self._save_tracker()
    
    def clear_all(self) -> None:
        """Clear all tracking data (for full reprocessing)"""
        logger.warning("Clearing all book tracking data")
        self.processed_books = {}
        self._save_tracker()
        logger.info("All book tracking data cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about processed books
        
        Returns:
            Dictionary with stats
        """
        total_chunks = sum(
            book.get('chunk_count', 0)
            for book in self.processed_books.values()
        )
        
        return {
            'total_books_processed': len(self.processed_books),
            'total_chunks': total_chunks,
            'books': list(self.processed_books.keys())
        }


# Example usage
if __name__ == "__main__":
    manager = BookManager()
    
    # Get new books
    new_books = manager.get_new_books()
    print(f"New books to process: {len(new_books)}")
    for book in new_books:
        print(f"  - {book.name}")
    
    # Get stats
    stats = manager.get_stats()
    print(f"\nStats: {stats}")
