"""
RAG Engine Module
Orchestrates retrieval and generation for the Chemical Engineering RAG system
"""

from typing import List, Dict, Any, Tuple
from src.vector_store import VectorStore
from src.llm_handler import LLMHandler
from utils.helpers import format_citations_list
from config.settings import settings
from utils.logger import get_logger, log_execution_time

# Initialize logger
logger = get_logger(__name__)


class RAGEngine:
    """Main RAG pipeline orchestrator"""
    
    def __init__(self):
        """Initialize RAG engine with vector store and LLM"""
        logger.info("Initializing RAG Engine...")
        
        # Initialize components
        try:
            self.vector_store = VectorStore()
            self.llm = LLMHandler()
            logger.info("RAG Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG Engine: {type(e).__name__}: {str(e)}")
            raise
    
    @log_execution_time
    def query_books(self, question: str, top_k: int = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Query the book-based RAG system
        
        Args:
            question: User question
            top_k: Number of chunks to retrieve
            
        Returns:
            Tuple of (answer, sources)
        """
        logger.info(f"Query (books mode) | Question: '{question[:50]}...' | Top-K: {top_k or settings.TOP_K_RESULTS}")
        
        # Retrieve relevant chunks
        chunks = self.vector_store.similarity_search(question, top_k=top_k)
        logger.debug(f"Retrieved {len(chunks)} chunks from vector store")
        
        if not chunks:
            logger.warning("No relevant chunks found for query")
            return "I couldn't find relevant information in the books to answer this question.", []
        
        # Generate response using LLM
        prompt = self.llm.create_rag_prompt(question, chunks)
        answer = self.llm.generate_response(prompt)
        
        # Format sources
        sources = [
            {
                'book': chunk['metadata'].get('book_name', 'Unknown'),
                'page': chunk['metadata'].get('page', 'N/A'),
                'text_preview': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text']
            }
            for chunk in chunks
        ]
        
        logger.info(f"Query completed | Answer length: {len(answer)} chars | Sources: {len(sources)}")
        return answer, sources
    
    def query_general_knowledge(self, question: str) -> str:
        """
        Query using general knowledge mode (LLM-based internet search alternative)
        
        Args:
            question: User question
            
        Returns:
            Answer based on LLM's general knowledge
        """
        logger.info(f"Query (general knowledge mode) | Question: '{question[:50]}...'")
        prompt = self.llm.create_general_knowledge_prompt(question)
        answer = self.llm.generate_response(prompt)
        logger.info(f"General knowledge query completed | Answer length: {len(answer)} chars")
        return answer
    
    @log_execution_time
    def query(self, question: str, use_general_knowledge: bool = False, top_k: int = None) -> Dict[str, Any]:
        """
        Main query interface - routes to book RAG or general knowledge
        
        Args:
            question: User question
            use_general_knowledge: If True, use general knowledge mode instead of books
            top_k: Number of chunks to retrieve (for book mode)
            
        Returns:
            Dictionary with answer, mode, and sources (if applicable)
        """
        mode = "general_knowledge" if use_general_knowledge else "book_based"
        logger.info(f"Query started | Mode: {mode} | Question: '{question[:30]}...'")
        
        if use_general_knowledge:
            # General knowledge mode
            answer = self.query_general_knowledge(question)
            return {
                'answer': answer,
                'mode': 'general_knowledge',
                'sources': [],
                'citations': "Based on general knowledge (not from textbooks)"
            }
        else:
            # Book-based RAG mode
            answer, sources = self.query_books(question, top_k)
            
            # Format citations
            citations = format_citations_list(sources)
            
            return {
                'answer': answer,
                'mode': 'book_based',
                'sources': sources,
                'citations': citations
            }
    
    def query_stream(self, question: str, use_general_knowledge: bool = False, top_k: int = None):
        """
        Stream query responses in real-time (for better UX)
        
        Args:
            question: User question
            use_general_knowledge: If True, use general knowledge mode instead of books
            top_k: Number of chunks to retrieve (for book mode)
            
        Yields:
            Response text chunks
            
        Returns:
            Final result dictionary with metadata
        """
        mode = "general_knowledge" if use_general_knowledge else "book_based"
        logger.info(f"Streaming query started | Mode: {mode} | Question: '{question[:30]}...'")
        
        if use_general_knowledge:
            # General knowledge mode - stream response
            prompt = self.llm.create_general_knowledge_prompt(question)
            
            full_answer = ""
            for chunk in self.llm.stream_response(prompt):
                full_answer += chunk
                yield chunk
            
            logger.info(f"Streaming query completed | Mode: {mode} | Answer length: {len(full_answer)} chars")
            return {
                'answer': full_answer,
                'mode': 'general_knowledge',
                'sources': [],
                'citations': "Based on general knowledge (not from textbooks)"
            }
        else:
            # Book-based RAG mode
            k = top_k or settings.TOP_K_RESULTS
            chunks = self.vector_store.similarity_search(question, top_k=k)
            
            if not chunks:
                error_msg = "No relevant information found in the books."
                logger.warning(error_msg)
                yield error_msg
                return {
                    'answer': error_msg,
                    'mode': 'book_based',
                    'sources': [],
                    'citations': ""
                }
            
            # Generate streaming response
            prompt = self.llm.create_rag_prompt(question, chunks)
            
            full_answer = ""
            for chunk in self.llm.stream_response(prompt):
                full_answer += chunk
                yield chunk
            
            # Extract sources
            sources = [
                {
                    'book': chunk['metadata'].get('book_name', 'Unknown'),
                    'page': int(chunk['metadata'].get('page', 0))
                }
                for chunk in chunks
            ]
            
            citations = format_citations_list(sources)
            
            logger.info(f"Streaming query completed | Mode: {mode} | Answer length: {len(full_answer)} chars | Sources: {len(sources)}")
            return {
                'answer': full_answer,
                'mode': 'book_based',
                'sources': sources,
                'citations': citations
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG system
        
        Returns:
            Dictionary with system statistics
        """
        logger.debug("Fetching system statistics")
        vector_stats = self.vector_store.get_collection_stats()
        
        stats = {
            'vector_store': vector_stats,
            'llm_model': settings.LLM_MODEL,
            'embedding_model': settings.EMBEDDING_MODEL,
            'chunk_size': settings.CHUNK_SIZE,
            'top_k': settings.TOP_K_RESULTS
        }
        logger.info(f"System stats retrieved | Total chunks: {vector_stats.get('total_chunks', 0)}")
        return stats
    
    def search_by_book(self, question: str, book_name: str, top_k: int = None) -> Dict[str, Any]:
        """
        Search within a specific book
        
        Args:
            question: User question
            book_name: Name of the book to search in
            top_k: Number of chunks to retrieve
            
        Returns:
            Dictionary with answer and sources from the specific book
        """
        logger.info(f"Book-specific query | Book: {book_name} | Question: '{question[:30]}...'")
        k = top_k or settings.TOP_K_RESULTS
        chunks = self.vector_store.search_by_book(question, book_name, top_k=k)
        
        if not chunks:
            logger.warning(f"No relevant information found in book: {book_name}")
            return {
                'answer': f"No relevant information found in '{book_name}'.",
                'mode': 'book_based',
                'sources': [],
                'citations': ""
            }
        
        # Generate response
        prompt = self.llm.create_rag_prompt(question, chunks)
        answer = self.llm.generate_response(prompt)
        
        # Extract sources
        sources = [
            {
                'book': chunk['metadata'].get('book_name', 'Unknown'),
                'page': int(chunk['metadata'].get('page', 0))
            }
            for chunk in chunks
        ]
        
        citations = format_citations_list(sources)
        
        logger.info(f"Book-specific query completed | Book: {book_name} | Sources: {len(sources)}")
        return {
            'answer': answer,
            'mode': 'book_based',
            'sources': sources,
            'citations': citations,
            'book_filter': book_name
        }


# Example usage
if __name__ == "__main__":
    try:
        rag = RAGEngine()
        
        # Get stats
        stats = rag.get_system_stats()
        print(f"System stats: {stats}")
        
        # Test query (will fail if no books are loaded)
        # result = rag.query("What is distillation?", use_general_knowledge=True)
        # print(f"Answer: {result['answer']}")
        
    except Exception as e:
        print(f"Error: {e}")
