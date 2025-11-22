"""
Vector Store Module
Manages ChromaDB for persistent vector storage and similarity search
"""

# Disable ChromaDB's default embedding function to avoid onnxruntime dependency
import os
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from config.settings import settings
from utils.logger import get_logger, log_execution_time

# Initialize logger
logger = get_logger(__name__)


class VectorStore:
    """Manage ChromaDB vector database for document retrieval"""
    
    def __init__(self):
        """Initialize ChromaDB with persistent storage"""
        logger.info("Initializing VectorStore...")
        
        # Initialize ChromaDB client with persistence
        # Use PersistentClient to avoid onnxruntime dependency
        try:
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY
            )
            logger.info(f"ChromaDB client initialized | Path: {settings.CHROMA_PERSIST_DIRECTORY}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {type(e).__name__}: {str(e)}")
            raise
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        try:
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Embedding model loaded successfully: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {type(e).__name__}: {str(e)}")
            raise
        
        # Get or create collection without default embedding function
        # We'll use sentence-transformers directly
        try:
            self.collection = self.client.get_collection(
                name=settings.CHROMA_COLLECTION_NAME
            )
            count = self.collection.count()
            logger.info(f"Loaded existing collection: {settings.CHROMA_COLLECTION_NAME} | Documents: {count}")
        except:
            self.collection = self.client.create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"description": "Chemical Engineering textbook embeddings"}
            )
            logger.info(f"Created new collection: {settings.CHROMA_COLLECTION_NAME}")
        
        logger.info("VectorStore initialization complete")
    
    @log_execution_time
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        logger.debug(f"Creating embeddings for {len(texts)} texts")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        logger.info(f"Created embeddings | Count: {len(texts)} | Dimensions: {len(embeddings[0]) if len(embeddings) > 0 else 0}")
        return embeddings.tolist()
    
    @log_execution_time
    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Add document chunks to ChromaDB
        
        Args:
            chunks: List of chunk dictionaries with 'text' and metadata
        """
        if not chunks:
            logger.warning("No chunks to add")
            return
        
        logger.info(f"Adding {len(chunks)} chunks to ChromaDB...")
        
        try:
            # Extract texts and metadata
            texts = [chunk['text'] for chunk in chunks]
            metadatas = [
                {
                    'book_name': chunk['book_name'],
                    'page': str(chunk['page']),
                    'chunk_id': str(chunk['chunk_id']),
                    'source': chunk['source']
                }
                for chunk in chunks
            ]
            
            # Generate unique IDs
            ids = [f"{chunk['book_name']}_chunk_{chunk['chunk_id']}" for chunk in chunks]
            logger.debug(f"Generated {len(ids)} unique IDs for chunks")
            
            # Create embeddings
            embeddings = self.create_embeddings(texts)
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully added {len(chunks)} chunks to ChromaDB | Total docs: {self.collection.count()}")
            
        except Exception as e:
            logger.error(f"Failed to add documents: {type(e).__name__}: {str(e)}")
            raise
    
    @log_execution_time
    def similarity_search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents using semantic similarity
        
        Args:
            query: Search query
            top_k: Number of results to return (default from settings)
            
        Returns:
            List of relevant chunks with metadata and scores
        """
        k = top_k or settings.TOP_K_RESULTS
        logger.debug(f"Similarity search | Query: '{query[:50]}...' | Top-K: {k}")
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
            
            logger.info(f"Search complete | Results: {len(formatted_results)} | Query: '{query[:30]}...'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {type(e).__name__}: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection
        
        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()
        
        return {
            'collection_name': settings.CHROMA_COLLECTION_NAME,
            'total_chunks': count,
            'embedding_model': settings.EMBEDDING_MODEL,
            'persist_directory': settings.CHROMA_PERSIST_DIRECTORY
        }
    
    def clear_collection(self) -> None:
        """Clear all documents from the collection"""
        logger.warning("Clearing collection...")
        try:
            # Delete and recreate collection
            self.client.delete_collection(settings.CHROMA_COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"description": "Chemical Engineering textbook embeddings"}
            )
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear collection: {type(e).__name__}: {str(e)}")
            raise
    
    @log_execution_time
    def search_by_book(self, query: str, book_name: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Search within a specific book
        
        Args:
            query: Search query
            book_name: Name of the book to search in
            top_k: Number of results
            
        Returns:
            List of relevant chunks from the specified book
        """
        k = top_k or settings.TOP_K_RESULTS
        logger.debug(f"Book-specific search | Book: {book_name} | Query: '{query[:50]}...' | Top-K: {k}")
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Search with metadata filter
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where={"book_name": book_name}
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
            
            logger.info(f"Book search complete | Book: {book_name} | Results: {len(formatted_results)}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Book search failed: {type(e).__name__}: {str(e)}")
            raise
    
    def get_all_book_names(self) -> List[str]:
        """
        Get list of all unique book names in the collection
        
        Returns:
            List of book names
        """
        logger.debug("Fetching all book names from collection")
        try:
            # Query all documents
            all_data = self.collection.get()
            
            if all_data['metadatas']:
                book_names = set()
                for metadata in all_data['metadatas']:
                    book_name = metadata.get('book_name')
                    if book_name:
                        book_names.add(book_name)
                logger.info(f"Found {len(book_names)} unique books in collection")
                return list(book_names)
            logger.info("No books found in collection")
            return []
        except Exception as e:
            logger.error(f"Error getting book names: {type(e).__name__}: {str(e)}")
            return []
    
    def has_book(self, book_name: str) -> bool:
        """
        Check if a book exists in the collection
        
        Args:
            book_name: Name of the book to check
            
        Returns:
            True if book exists in collection
        """
        logger.debug(f"Checking if book exists: {book_name}")
        try:
            results = self.collection.get(
                where={"book_name": book_name},
                limit=1
            )
            exists = len(results['ids']) > 0
            logger.debug(f"Book '{book_name}' exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking for book: {type(e).__name__}: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    vector_store = VectorStore()
    
    # Get stats
    stats = vector_store.get_collection_stats()
    print(f"Collection stats: {stats}")
