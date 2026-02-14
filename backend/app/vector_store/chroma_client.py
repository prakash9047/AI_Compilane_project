"""
ChromaDB client for vector storage and retrieval.
"""
import chromadb
from typing import List, Dict
from loguru import logger

from app.core.config import settings as app_settings


class ChromaClient:
    """ChromaDB client for document embeddings and semantic search."""
    
    def __init__(self):
        """Initialize ChromaDB client."""
        # Use PersistentClient for proper persistence
        self.client = chromadb.PersistentClient(
            path=app_settings.CHROMA_PERSIST_DIRECTORY
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=app_settings.CHROMA_COLLECTION_NAME,
            metadata={"description": "Compliance document embeddings"}
        )
        
        logger.info(f"ChromaDB initialized: {app_settings.CHROMA_COLLECTION_NAME}")
        logger.info(f"Collection count: {self.collection.count()}")

    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ):
        """Add documents to the collection."""
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to ChromaDB")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def query(
        self,
        query_texts: List[str],
        n_results: int = 10,
        where: Dict = None
    ) -> Dict:
        """Query the collection."""
        try:
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where
            )
            logger.debug(f"Query returned {len(results['ids'][0])} results")
            return results
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def delete_by_document_id(self, document_id: int):
        """Delete all segments for a document."""
        try:
            self.collection.delete(
                where={"document_id": document_id}
            )
            logger.info(f"Deleted segments for document {document_id}")
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise
