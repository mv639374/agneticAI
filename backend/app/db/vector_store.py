# agenticAI/backend/app/db/vector_store.py

"""
Vector Store Integration for Semantic Search

This module provides vector database integration for:
1. Storing conversation embeddings for semantic search
2. Agent memory - finding relevant past conversations
3. Document embeddings for RAG (Retrieval-Augmented Generation)

Supported Vector DBs:
- Pinecone (cloud, free tier available)
- ChromaDB (self-hosted or cloud)

Key Concepts:
- Embeddings: Vector representations of text (created by LLMs)
- Semantic search: Find similar text based on meaning, not keywords
- Namespaces: Logical separation of vectors (e.g., by user)
"""

from typing import Any, Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

try:
    from langchain_chroma import Chroma
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)


# =============================================================================
# EMBEDDING MODEL INITIALIZATION
# =============================================================================

def get_embedding_model():
    """
    Get embedding model based on configured LLM provider.
    
    Embeddings convert text to vectors (numerical representations).
    Same text always produces same vector, enabling semantic similarity search.
    
    Providers:
    - Google (text-embedding-004): 768 dimensions, good quality
    - Groq: Uses local sentence-transformers (Groq doesn't provide embeddings API)
    
    Returns:
        Embedding model instance
    """
    if settings.DEFAULT_LLM_PROVIDER == "google":
        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GOOGLE_API_KEY,
        )
    else:
        # Groq doesn't provide embeddings API, so we use sentence-transformers locally
        # This is faster and doesn't consume API quota
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},  # Change to "cuda" for GPU
            encode_kwargs={"normalize_embeddings": True},
        )


# =============================================================================
# VECTOR STORE MANAGER
# =============================================================================

class VectorStoreManager:
    """
    Manages vector database operations for semantic search.
    Provides unified interface for Pinecone and ChromaDB.
    """
    
    def __init__(self):
        self.vector_store: Optional[Any] = None
        self.embeddings = None
    
    async def initialize(self) -> None:
        """
        Initialize vector store based on configuration.
        Creates index/collection if it doesn't exist.
        """
        self.embeddings = get_embedding_model()
        
        if settings.VECTOR_DB_TYPE == "pinecone":
            await self._init_pinecone()
        elif settings.VECTOR_DB_TYPE == "chromadb":
            await self._init_chromadb()
        else:
            raise ValueError(f"Unsupported vector DB: {settings.VECTOR_DB_TYPE}")
        
        log.info("Vector store initialized", db_type=settings.VECTOR_DB_TYPE)
    
    async def _init_pinecone(self) -> None:
        """
        Initialize Pinecone vector store.
        
        Pinecone is a managed vector database with:
        - Free tier: 1 index, 100K vectors
        - Serverless: Auto-scaling
        - Low latency: Global deployment
        """
        from pinecone import Pinecone, ServerlessSpec
        
        # Initialize Pinecone client
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Create index if it doesn't exist
        index_name = settings.PINECONE_INDEX_NAME
        if index_name not in pc.list_indexes().names():
            log.info("Creating Pinecone index", index=index_name)
            
            # Get embedding dimension (768 for text-embedding-004, 384 for MiniLM)
            dimension = 768 if settings.DEFAULT_LLM_PROVIDER == "google" else 384
            
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",  # Similarity metric
                spec=ServerlessSpec(
                    cloud="aws",
                    region=settings.PINECONE_ENVIRONMENT,
                ),
            )
            log.info("Pinecone index created")
        
        # Initialize LangChain vector store
        self.vector_store = PineconeVectorStore(
            index_name=index_name,
            embedding=self.embeddings,
        )
    
    async def _init_chromadb(self) -> None:
        """
        Initialize ChromaDB vector store.
        
        ChromaDB is an open-source vector database with:
        - Self-hosted or cloud
        - Embedded mode for development
        - Persistent storage
        """
        if not CHROMA_AVAILABLE:
            raise ImportError("ChromaDB not installed. Run: uv pip install chromadb")
        
        # Use persistent storage in data directory
        persist_directory = "data/chromadb"
        
        self.vector_store = Chroma(
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=persist_directory,
        )
        log.info("ChromaDB initialized", persist_dir=persist_directory)
    
    async def add_texts(
        self,
        texts: list[str],
        metadatas: Optional[list[dict]] = None,
        namespace: Optional[str] = None,
    ) -> list[str]:
        """
        Add texts to vector store.
        
        Args:
            texts: List of text strings to embed and store
            metadatas: Optional metadata for each text
            namespace: Logical separation (e.g., user ID, conversation ID)
        
        Returns:
            List of document IDs
        """
        if not self.vector_store:
            raise RuntimeError("Vector store not initialized")
        
        ids = await self.vector_store.aadd_texts(
            texts=texts,
            metadatas=metadatas,
        )
        log.info("Texts added to vector store", count=len(texts), namespace=namespace)
        return ids
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        namespace: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for similar texts.
        
        Args:
            query: Search query text
            k: Number of results to return
            namespace: Search within specific namespace
        
        Returns:
            List of similar documents with metadata
        """
        if not self.vector_store:
            raise RuntimeError("Vector store not initialized")
        
        results = await self.vector_store.asimilarity_search(
            query=query,
            k=k,
        )
        log.debug("Similarity search completed", query=query[:50], results=len(results))
        return results


# =============================================================================
# GLOBAL VECTOR STORE INSTANCE
# =============================================================================

vector_store_manager = VectorStoreManager()


async def init_vector_store() -> None:
    """Initialize vector store. Call at application startup."""
    await vector_store_manager.initialize()


async def close_vector_store() -> None:
    """Cleanup vector store. Call at application shutdown."""
    # No cleanup needed for current implementations
    log.info("Vector store closed")
