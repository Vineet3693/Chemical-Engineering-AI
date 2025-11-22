"""
Document Processing Module
Handles PDF extraction, text chunking, and metadata management for Chemical Engineering books
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any, Tuple
from utils.helpers import clean_text, extract_book_name
from config.settings import settings
from utils.logger import get_logger, log_execution_time, LogContext

# Initialize logger
logger = get_logger(__name__)


class DocumentProcessor:
    """Process PDF documents for RAG system"""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize document processor
        
        Args:
            chunk_size: Size of text chunks (default from settings)
            chunk_overlap: Overlap between chunks (default from settings)
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        logger.info(f"DocumentProcessor initialized | Chunk size: {self.chunk_size} | Overlap: {self.chunk_overlap}")
    
    @log_execution_time
    def load_pdf(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text and metadata from a PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        pdf_path = Path(file_path)
        logger.debug(f"Loading PDF: {pdf_path.name}")
        
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {file_path}")
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        try:
            # Open PDF
            doc = fitz.open(file_path)
            page_count = len(doc)
            logger.info(f"Opened PDF: {pdf_path.name} | Pages: {page_count}")
            
            # Extract text from all pages
            full_text = ""
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                full_text += f"\n--- Page {page_num} ---\n{text}"
                if page_num % 10 == 0:
                    logger.debug(f"Extracted text from {page_num}/{page_count} pages")
            
            # Extract metadata
            metadata = {
                'book_name': extract_book_name(file_path),
                'file_path': str(pdf_path),
                'total_pages': page_count,
                'title': doc.metadata.get('title', extract_book_name(file_path)),
                'author': doc.metadata.get('author', 'Unknown')
            }
            
            doc.close()
            
            # Clean text
            full_text = clean_text(full_text)
            text_length = len(full_text)
            logger.info(f"PDF loaded successfully: {pdf_path.name} | Text length: {text_length:,} chars")
            
            return full_text, metadata
            
        except Exception as e:
            logger.error(f"Error loading PDF {pdf_path.name}: {type(e).__name__}: {str(e)}")
            raise
    
    @log_execution_time
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Full text to chunk
            metadata: Document metadata
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        logger.debug(f"Chunking text for: {metadata.get('book_name', 'Unknown')}")
        chunks = []
        
        # Simple character-based chunking (can be improved with token-based)
        # Approximate: 1 token ≈ 4 characters
        char_chunk_size = self.chunk_size * 4
        char_overlap = self.chunk_overlap * 4
        
        # Split by pages first to maintain page references
        pages = text.split('--- Page ')
        
        current_chunk = ""
        current_page = 1
        chunk_id = 0
        
        for page_section in pages[1:]:  # Skip first empty split
            # Extract page number
            try:
                page_num_str = page_section.split(' ---')[0]
                page_num = int(page_num_str)
                page_text = page_section.split('---\n', 1)[1] if '---\n' in page_section else page_section
            except (ValueError, IndexError):
                continue
            
            # Add page text to current chunk
            current_chunk += page_text
            
            # If chunk is large enough, create a chunk
            while len(current_chunk) >= char_chunk_size:
                chunk_text = current_chunk[:char_chunk_size]
                
                # Create chunk with metadata
                chunks.append({
                    'text': chunk_text.strip(),
                    'chunk_id': chunk_id,
                    'book_name': metadata['book_name'],
                    'page': page_num,
                    'source': metadata['file_path']
                })
                
                # Move to next chunk with overlap
                current_chunk = current_chunk[char_chunk_size - char_overlap:]
                chunk_id += 1
        
        # Add remaining text as final chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'chunk_id': chunk_id,
                'book_name': metadata['book_name'],
                'page': page_num,
                'source': metadata['file_path']
            })
        
        avg_chunk_size = sum(len(c['text']) for c in chunks) / len(chunks) if chunks else 0
        logger.info(f"Created {len(chunks)} chunks | Avg size: {avg_chunk_size:.0f} chars | Book: {metadata.get('book_name', 'Unknown')}")
        
        return chunks
    
    @log_execution_time
    def process_book(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a single book: extract text and create chunks
        
        Args:
            file_path: Path to PDF book
            
        Returns:
            List of text chunks with metadata
        """
        book_name = Path(file_path).name
        logger.info(f"Processing book: {book_name}")
        
        try:
            # Extract text and metadata
            text, metadata = self.load_pdf(file_path)
            
            # Create chunks
            chunks = self.chunk_text(text, metadata)
            
            logger.info(f"Book processed successfully: {book_name} | Chunks: {len(chunks)} | Pages: {metadata['total_pages']}")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to process book {book_name}: {type(e).__name__}: {str(e)}")
            raise
    
    @log_execution_time
    def process_books_directory(self, directory: str = None) -> List[Dict[str, Any]]:
        """
        Process all PDF books in a directory
        
        Args:
            directory: Path to directory containing PDFs (default: settings.BOOKS_DIR)
            
        Returns:
            List of all chunks from all books
        """
        books_dir = Path(directory) if directory else settings.BOOKS_DIR
        logger.info(f"Processing books directory: {books_dir}")
        
        if not books_dir.exists():
            logger.error(f"Books directory not found: {books_dir}")
            raise FileNotFoundError(f"Books directory not found: {books_dir}")
        
        # Get all PDF files
        pdf_files = list(books_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {books_dir}")
            raise ValueError(f"No PDF files found in {books_dir}")
        
        logger.info(f"Found {len(pdf_files)} PDF books to process")
        
        # Process all books
        all_chunks = []
        successful = 0
        failed = 0
        
        for i, pdf_file in enumerate(pdf_files, 1):
            try:
                logger.info(f"Processing book {i}/{len(pdf_files)}: {pdf_file.name}")
                chunks = self.process_book(str(pdf_file))
                all_chunks.extend(chunks)
                successful += 1
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {type(e).__name__}: {str(e)}")
                failed += 1
                continue
        
        logger.info(f"Batch processing complete | Total chunks: {len(all_chunks)} | Successful: {successful} | Failed: {failed}")
        
        return all_chunks
    
    @log_execution_time
    def process_new_books(self, book_manager, directory: str = None) -> Dict[str, Any]:
        """
        Process only new books that haven't been processed yet
        
        Args:
            book_manager: BookManager instance for tracking
            directory: Path to directory containing PDFs (default: settings.BOOKS_DIR)
            
        Returns:
            Dictionary with processing results
        """
        books_dir = Path(directory) if directory else settings.BOOKS_DIR
        logger.info(f"Scanning for new books in: {books_dir}")
        
        if not books_dir.exists():
            logger.warning(f"Books directory does not exist: {books_dir}")
            return {
                'new_books_processed': 0,
                'skipped_books': 0,
                'total_new_chunks': 0,
                'chunks': []
            }
        
        # Get all PDF files
        all_pdfs = list(books_dir.glob("*.pdf"))
        logger.info(f"Found {len(all_pdfs)} PDF books in directory")
        
        # Separate new and already processed books
        new_books = []
        skipped_books = []
        
        for pdf_file in all_pdfs:
            if book_manager.is_processed(pdf_file):
                skipped_books.append(pdf_file.name)
                logger.debug(f"Skipping already processed: {pdf_file.name}")
            else:
                new_books.append(pdf_file)
                logger.info(f"New book detected: {pdf_file.name}")
        
        logger.info(f"New books: {len(new_books)} | Already processed: {len(skipped_books)}")
        
        # Process new books
        all_chunks = []
        for i, pdf_file in enumerate(new_books, 1):
            try:
                logger.info(f"Processing NEW book {i}/{len(new_books)}: {pdf_file.name}")
                chunks = self.process_book(str(pdf_file))
                all_chunks.extend(chunks)
                
                # Mark as processed
                book_manager.mark_as_processed(pdf_file, len(chunks))
                logger.info(f"Marked as processed: {pdf_file.name} | Chunks: {len(chunks)}")
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {type(e).__name__}: {str(e)}")
                continue
        
        result = {
            'new_books_processed': len(new_books),
            'skipped_books': len(skipped_books),
            'total_new_chunks': len(all_chunks),
            'chunks': all_chunks,
            'new_book_names': [b.name for b in new_books],
            'skipped_book_names': skipped_books
        }
        
        logger.info(f"New book processing complete | Processed: {len(new_books)} | Total new chunks: {len(all_chunks)}")
        
        return result


# Example usage
if __name__ == "__main__":
    processor = DocumentProcessor()
    
    # Process all books in the default directory
    try:
        chunks = processor.process_books_directory()
        print(f"\nSuccessfully processed books!")
        print(f"Sample chunk: {chunks[0]}")
    except Exception as e:
        print(f"Error: {e}")
