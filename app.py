"""
Chemical Engineering RAG System - Main Streamlit Application
A RAG application for Chemical Engineering with book-based retrieval and general knowledge mode
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.document_processor import DocumentProcessor
from src.book_manager import BookManager
from src.rag_engine import RAGEngine
from src.export_handler import ExportHandler
from config.settings import settings
from utils.helpers import get_timestamp, truncate_text
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Chemical Engineering RAG",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .source-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .book-mode {
        background-color: #d4edda;
        color: #155724;
    }
    .general-mode {
        background-color: #d1ecf1;
        color: #0c5460;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'rag_engine' not in st.session_state:
        st.session_state.rag_engine = None
        logger.debug("Initialized session state: rag_engine")
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        logger.debug("Initialized session state: chat_history")
    
    if 'current_response' not in st.session_state:
        st.session_state.current_response = None
        logger.debug("Initialized session state: current_response")
    
    if 'auto_init_done' not in st.session_state:
        st.session_state.auto_init_done = False
        logger.debug("Initialized session state: auto_init_done")


def auto_initialize_system():
    """Auto-initialize RAG system and process new books on startup"""
    if st.session_state.auto_init_done:
        return
    
    logger.info("Starting auto-initialization...")
    
    # Initialize RAG engine
    if st.session_state.rag_engine is None:
        try:
            with st.spinner("🚀 Initializing RAG system..."):
                st.session_state.rag_engine = RAGEngine()
                logger.info("RAG engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {type(e).__name__}: {str(e)}")
            st.error(f"Error initializing RAG system: {e}")
            return
    
    # Auto-process new books
    try:
        book_manager = BookManager()
        processor = DocumentProcessor()
        
        # Check for new books
        new_books = book_manager.get_new_books()
        logger.info(f"Found {len(new_books)} new books to process")
        
        if new_books:
            with st.spinner(f"📚 Processing {len(new_books)} new book(s)..."):
                result = processor.process_new_books(book_manager)
                
                # Add new chunks to vector store
                if result['total_new_chunks'] > 0:
                    st.session_state.rag_engine.vector_store.add_documents(result['chunks'])
                    logger.info(f"Auto-initialization complete | New books: {result['new_books_processed']} | Chunks: {result['total_new_chunks']}")
                    
                    st.success(
                        f"✅ Processed {result['new_books_processed']} new book(s) "
                        f"({result['total_new_chunks']} chunks)"
                    )
                    
                    if result['skipped_books'] > 0:
                        st.info(f"⏭️ Skipped {result['skipped_books']} already-processed book(s)")
        else:
            # All books already processed
            stats = book_manager.get_stats()
            if stats['total_books_processed'] > 0:
                logger.info(f"All books already processed | Books: {stats['total_books_processed']} | Chunks: {stats['total_chunks']}")
                st.success(
                    f"✅ System ready! {stats['total_books_processed']} book(s) loaded "
                    f"({stats['total_chunks']} chunks)"
                )
    
    except Exception as e:
        logger.warning(f"Auto-initialization note: {type(e).__name__}: {str(e)}")
        st.warning(f"Note: {e}")
    
    st.session_state.auto_init_done = True
    logger.info("Auto-initialization finished")


def rescan_for_new_books():
    """Manually rescan for new books"""
    logger.info("Manual rescan initiated")
    try:
        book_manager = BookManager()
        processor = DocumentProcessor()
        
        with st.spinner("🔍 Scanning for new books..."):
            result = processor.process_new_books(book_manager)
            
            if result['total_new_chunks'] > 0:
                st.session_state.rag_engine.vector_store.add_documents(result['chunks'])
                logger.info(f"Rescan complete | New books: {result['new_books_processed']} | Chunks: {result['total_new_chunks']}")
                st.success(
                    f"✅ Processed {result['new_books_processed']} new book(s) "
                    f"({result['total_new_chunks']} chunks)"
                )
            else:
                logger.info("Rescan complete | No new books found")
                st.info("No new books found. All books are already processed!")
    
    except Exception as e:
        logger.error(f"Rescan failed: {type(e).__name__}: {str(e)}")
        st.error(f"Error rescanning: {e}")


def reprocess_all_books():
    """Reprocess all books (clear and rebuild)"""
    logger.warning("Reprocess all books initiated")
    try:
        book_manager = BookManager()
        
        with st.spinner("🔄 Clearing existing data..."):
            # Clear vector store
            st.session_state.rag_engine.vector_store.clear_collection()
            # Clear book tracker
            book_manager.clear_all()
            logger.info("Cleared all existing data")
        
        with st.spinner("📚 Reprocessing all books..."):
            processor = DocumentProcessor()
            result = processor.process_new_books(book_manager)
            
            if result['total_new_chunks'] > 0:
                st.session_state.rag_engine.vector_store.add_documents(result['chunks'])
                logger.info(f"Reprocess complete | Books: {result['new_books_processed']} | Chunks: {result['total_new_chunks']}")
                st.success(
                    f"✅ Reprocessed {result['new_books_processed']} book(s) "
                    f"({result['total_new_chunks']} chunks)"
                )
            else:
                logger.warning("Reprocess complete | No books found")
                st.warning("No books found in the books directory!")
    
    except Exception as e:
        logger.error(f"Reprocess failed: {type(e).__name__}: {str(e)}")
        st.error(f"Error reprocessing: {e}")


def main():
    """Main application"""
    logger.info("=" * 50)
    logger.info("Chemical Engineering RAG Application Started")
    logger.info("=" * 50)
    
    initialize_session_state()
    
    # Auto-initialize on first run
    auto_initialize_system()
    
    # Header
    st.markdown('<h1 class="main-header">🧪 Chemical Engineering RAG System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ask questions about Chemical Engineering from textbooks or general knowledge</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ System Status")
        
        # System stats
        if st.session_state.rag_engine:
            stats = st.session_state.rag_engine.get_system_stats()
            st.metric("Total Chunks", stats['vector_store']['total_chunks'])
            
            # Book manager stats
            book_manager = BookManager()
            book_stats = book_manager.get_stats()
            st.metric("Processed Books", book_stats['total_books_processed'])
        
        st.divider()
        
        # Book management
        st.header("📚 Book Management")
        
        books_count = settings.get_books_count()
        st.info(f"📁 Books in directory: {books_count}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Rescan", help="Scan for new books"):
                rescan_for_new_books()
        
        with col2:
            if st.button("🔄 Reprocess All", help="Clear and reprocess all books"):
                if st.session_state.rag_engine:
                    reprocess_all_books()
        
        st.divider()
        
        # Query mode
        st.header("🔍 Query Mode")
        use_general = st.toggle(
            "Use General Knowledge",
            value=False,
            help="Toggle between book-based RAG and general knowledge mode"
        )
        
        if use_general:
            st.info("🌐 General Knowledge Mode")
        else:
            st.info("📖 Book-Based RAG Mode")
        
        st.divider()
        
        # Export options
        st.header("📥 Export")
        
        if st.session_state.current_response:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 PDF"):
                    exporter = ExportHandler()
                    try:
                        resp = st.session_state.current_response
                        pdf_path = exporter.export_to_pdf(
                            resp['query'],
                            resp['answer'],
                            resp['citations'],
                            resp['mode']
                        )
                        
                        with open(pdf_path, 'rb') as f:
                            st.download_button(
                                "⬇️ Download PDF",
                                f,
                                file_name=Path(pdf_path).name,
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"Export error: {e}")
            
            with col2:
                if st.button("📝 DOCX"):
                    exporter = ExportHandler()
                    try:
                        resp = st.session_state.current_response
                        docx_path = exporter.export_to_docx(
                            resp['query'],
                            resp['answer'],
                            resp['citations'],
                            resp['mode']
                        )
                        
                        with open(docx_path, 'rb') as f:
                            st.download_button(
                                "⬇️ Download DOCX",
                                f,
                                file_name=Path(docx_path).name,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                    except Exception as e:
                        st.error(f"Export error: {e}")
        else:
            st.info("Submit a query to enable export")
    
    # Main content area
    if st.session_state.rag_engine is None:
        st.warning("⚠️ System initialization failed. Please check the sidebar for errors.")
        return
    
    # Query input
    st.header("💬 Ask a Question")
    
    query = st.text_area(
        "Enter your Chemical Engineering question:",
        height=100,
        placeholder="e.g., What is distillation and how does it work?"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        submit_button = st.button("🔍 Get Answer", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🗑️ Clear History", use_container_width=True):
            logger.info("Chat history cleared by user")
            st.session_state.chat_history = []
            st.session_state.current_response = None
            st.rerun()
    
    # Process query
    if submit_button and query:
        logger.info(f"User query submitted | Mode: {'general' if use_general else 'books'} | Query: '{query[:50]}...'")
        try:
            # Create placeholder for streaming response
            answer_placeholder = st.empty()
            
            # Use streaming query
            stream_generator = st.session_state.rag_engine.query_stream(
                query,
                use_general_knowledge=use_general
            )
            
            # Display streaming response manually
            answer_text = ""
            answer_placeholder.markdown("### 🤖 Generating Answer...")
            
            for chunk in stream_generator:
                answer_text += chunk
                # Update the display with accumulated text
                answer_placeholder.markdown(f"### 🤖 Answer\n\n{answer_text}")
            
            logger.info(f"Query completed | Answer length: {len(answer_text)} chars")
            
            # Construct final result
            result = {
                'answer': answer_text,
                'query': query,
                'mode': 'general_knowledge' if use_general else 'book_based',
                'sources': [],
                'citations': "Based on general knowledge (not from textbooks)" if use_general else ""
            }
            
            # For book-based mode, get sources
            if not use_general:
                # Re-run query to get sources (non-streaming)
                full_result = st.session_state.rag_engine.query(query, use_general_knowledge=False)
                result['sources'] = full_result.get('sources', [])
                result['citations'] = full_result.get('citations', '')
                logger.debug(f"Retrieved {len(result['sources'])} sources for query")
            
            # Store current response
            st.session_state.current_response = result
            
            # Add to history
            st.session_state.chat_history.append(result)
            
            # Clear placeholder and rerun to show final formatted response
            answer_placeholder.empty()
            st.rerun()
            
        except Exception as e:
            logger.error(f"Query processing error: {type(e).__name__}: {str(e)}")
            st.error(f"Error: {e}")
            import traceback
            st.error(traceback.format_exc())
    
    # Display current response
    if st.session_state.current_response:
        st.divider()
        
        resp = st.session_state.current_response
        
        # Mode badge
        if resp['mode'] == 'book_based':
            st.markdown('<span class="source-badge book-mode">📖 Book-Based Answer</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="source-badge general-mode">🌐 General Knowledge</span>', unsafe_allow_html=True)
        
        # Answer
        st.subheader("Answer")
        st.write(resp['answer'])
        
        # Citations
        if resp['citations']:
            with st.expander("📚 References", expanded=True):
                st.markdown(resp['citations'])
    
    # Chat history
    if st.session_state.chat_history:
        st.divider()
        st.header("📜 Chat History")
        
        for i, item in enumerate(reversed(st.session_state.chat_history[:-1]), 1):
            with st.expander(f"Q{len(st.session_state.chat_history) - i}: {truncate_text(item['query'], 60)}"):
                st.write(f"**Mode:** {item['mode'].replace('_', ' ').title()}")
                st.write(f"**Answer:** {item['answer']}")
                if item['citations']:
                    st.write(f"**References:** {item['citations']}")


if __name__ == "__main__":
    main()
