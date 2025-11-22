"""
Utility helper functions for the Chemical Engineering RAG System
"""

import re
from datetime import datetime
from typing import List, Dict, Any


def clean_text(text: str) -> str:
    """
    Clean and normalize text extracted from PDFs
    
    Args:
        text: Raw text string
        
    Returns:
        Cleaned text string
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page numbers (common patterns)
    text = re.sub(r'\n\d+\n', '\n', text)
    
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def format_citation(book_name: str, page_number: int = None) -> str:
    """
    Format a citation for a book reference
    
    Args:
        book_name: Name of the book
        page_number: Page number (optional)
        
    Returns:
        Formatted citation string
    """
    if page_number:
        return f"**{book_name}** (Page {page_number})"
    return f"**{book_name}**"


def format_citations_list(sources: List[Dict[str, Any]]) -> str:
    """
    Format a list of citations
    
    Args:
        sources: List of source dictionaries with 'book' and 'page' keys
        
    Returns:
        Formatted citations as markdown string
    """
    if not sources:
        return ""
    
    citations = []
    for i, source in enumerate(sources, 1):
        book = source.get('book', 'Unknown')
        page = source.get('page')
        citations.append(f"{i}. {format_citation(book, page)}")
    
    return "\n".join(citations)


def validate_pdf(file_path: str) -> bool:
    """
    Validate if a file is a PDF
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if valid PDF, False otherwise
    """
    return file_path.lower().endswith('.pdf')


def get_timestamp() -> str:
    """
    Get current timestamp in readable format
    
    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to specified length with ellipsis
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def extract_book_name(file_path: str) -> str:
    """
    Extract book name from file path
    
    Args:
        file_path: Path to the book file
        
    Returns:
        Book name without extension
    """
    from pathlib import Path
    return Path(file_path).stem


def format_response_metadata(query: str, mode: str, timestamp: str = None) -> Dict[str, str]:
    """
    Create metadata dictionary for a response
    
    Args:
        query: User query
        mode: Response mode ('book' or 'general')
        timestamp: Optional timestamp
        
    Returns:
        Metadata dictionary
    """
    return {
        'query': query,
        'mode': mode,
        'timestamp': timestamp or get_timestamp()
    }
