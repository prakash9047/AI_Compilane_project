"""
Chat API endpoints for RAG-based question answering.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

from app.services.chat_service import chat_service
from loguru import logger


router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat."""
    question: str = Field(..., description="User's question")
    session_id: str = Field(default="default", description="Conversation session ID")
    document_id: Optional[int] = Field(None, description="Filter by specific document")
    n_results: int = Field(default=5, description="Number of chunks to retrieve")


class ChatResponse(BaseModel):
    """Response model for chat."""
    answer: str
    sources: List[Dict]
    session_id: str
    timestamp: str
    chunks_retrieved: int
    model: str
    tokens_used: Optional[int] = 0


class ConversationHistory(BaseModel):
    """Conversation history model."""
    session_id: str
    messages: List[Dict]


@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """
    Ask a question using RAG-based chatbot.
    
    The system will:
    1. Search for relevant document chunks
    2. Use LLM to generate an answer based on context
    3. Return answer with source citations
    """
    try:
        result = await chat_service.ask_question(
            question=request.question,
            session_id=request.session_id,
            document_id=request.document_id,
            n_results=request.n_results
        )
        return result
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(session_id: str):
    """Get conversation history for a session."""
    try:
        messages = chat_service.get_conversation_history(session_id)
        return {
            "session_id": session_id,
            "messages": messages
        }
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session."""
    try:
        chat_service.clear_conversation(session_id)
        return {"message": f"Conversation {session_id} cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def chat_health():
    """Health check for chat service."""
    return {
        "status": "healthy",
        "service": "chat",
        "rag_enabled": True,
        "llm_enabled": True
    }
