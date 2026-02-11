"""
RAG (Retrieval-Augmented Generation) pipeline.
Implements semantic search and context-aware retrieval.
"""
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from loguru import logger

from app.core.config import settings
from app.vector_store.chroma_client import ChromaClient


class RAGPipeline:
    """RAG pipeline for semantic document search and retrieval."""
    
    def __init__(self):
        """Initialize RAG pipeline."""
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.chroma_client = ChromaClient()
        logger.info(f"RAG pipeline initialized with model: {settings.EMBEDDING_MODEL}")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        embedding = self.embedding_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def embed_segments(self, segments: List[Dict]) -> List[List[float]]:
        """Generate embeddings for document segments."""
        texts = [seg.get("content", "") for seg in segments]
        embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()
    
    async def index_document(self, document_id: int, segments: List[Dict]):
        """Index document segments in vector store."""
        logger.info(f"Indexing document {document_id} with {len(segments)} segments")
        
        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for i, segment in enumerate(segments):
            segment_id = f"doc_{document_id}_seg_{i}"
            
            documents.append(segment.get("content", ""))
            metadatas.append({
                "document_id": document_id,
                "segment_index": i,
                "type": segment.get("type", "unknown"),
                "title": segment.get("title", ""),
                "semantic_type": segment.get("semantic_type", "paragraph")
            })
            ids.append(segment_id)
        
        # Add to ChromaDB
        self.chroma_client.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Document {document_id} indexed successfully")
    
    async def search(
        self,
        query: str,
        n_results: int = 10,
        document_id: int = None
    ) -> List[Dict]:
        """
        Semantic search across indexed documents.
        
        Args:
            query: Search query
            n_results: Number of results to return
            document_id: Optional filter by document ID
            
        Returns:
            List of search results with metadata
        """
        logger.info(f"Searching for: {query}")
        
        # Build filter
        where_filter = {"document_id": document_id} if document_id else None
        
        # Query ChromaDB
        results = self.chroma_client.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })
        
        logger.info(f"Found {len(formatted_results)} results")
        return formatted_results
