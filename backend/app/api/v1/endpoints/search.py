"""
Semantic search API endpoints using RAG.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.engines.rag.rag_pipeline import RAGPipeline
from loguru import logger

router = APIRouter()

# Initialize RAG pipeline
rag_pipeline = RAGPipeline()


@router.get("/")
async def search_documents(
    query: str = Query(..., min_length=3, description="Search query"),
    document_id: Optional[int] = Query(None, description="Filter by document ID"),
    n_results: int = Query(10, ge=1, le=50, description="Number of results")
):
    """
    Semantic search across indexed documents.
    
    Args:
        query: Search query
        document_id: Optional document ID filter
        n_results: Number of results to return (1-50)
    """
    try:
        results = await rag_pipeline.search(
            query=query,
            n_results=n_results,
            document_id=document_id
        )
        
        return {
            "query": query,
            "total_results": len(results),
            "results": results
        }
    
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.post("/ask")
async def ask_question(
    question: str,
    document_id: Optional[int] = None
):
    """
    Ask a question about documents using RAG.
    
    This endpoint retrieves relevant context and generates an answer.
    """
    try:
        # Retrieve relevant context
        context_results = await rag_pipeline.search(
            query=question,
            n_results=5,
            document_id=document_id
        )
        
        # For now, return the context
        # In production, you would pass this to an LLM for answer generation
        return {
            "question": question,
            "context": context_results,
            "answer": "Answer generation not yet implemented. Use the context above."
        }
    
    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        raise HTTPException(status_code=500, detail="Question answering failed")
