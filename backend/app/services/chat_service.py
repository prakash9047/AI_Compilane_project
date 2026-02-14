"""
Chat service for managing conversations and integrating RAG + LLM.
"""
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from app.engines.rag.rag_pipeline import RAGPipeline
from app.services.llm_service import llm_service


class ChatService:
    """Service for managing chat conversations with RAG."""
    
    def __init__(self):
        """Initialize chat service."""
        self.rag_pipeline = RAGPipeline()
        self.conversations: Dict[str, List[Dict]] = {}  # In-memory storage
        logger.info("Chat service initialized")
    
    async def ask_question(
        self,
        question: str,
        session_id: str = "default",
        document_id: Optional[int] = None,
        n_results: int = 5
    ) -> Dict:
        """
        Process a question using RAG pipeline and LLM.
        
        Args:
            question: User's question
            session_id: Conversation session ID
            document_id: Optional filter by specific document
            n_results: Number of chunks to retrieve
            
        Returns:
            Dict with answer, sources, and metadata
        """
        try:
            logger.info(f"Processing question for session {session_id}: {question}")
            
            # Step 1: Retrieve relevant chunks using semantic search
            retrieved_chunks = await self.rag_pipeline.search(
                query=question,
                n_results=n_results,
                document_id=document_id
            )
            
            logger.info(f"Retrieved {len(retrieved_chunks)} chunks")
            
            # Step 2: Get conversation history
            history = self.get_conversation_history(session_id)
            
            # Step 3: Generate answer using LLM
            result = await llm_service.generate_answer(
                question=question,
                context_chunks=retrieved_chunks,
                conversation_history=history
            )
            
            # Step 4: Store in conversation history
            self._add_to_history(session_id, "user", question)
            self._add_to_history(session_id, "assistant", result["answer"])
            
            # Add metadata
            result["session_id"] = session_id
            result["timestamp"] = datetime.utcnow().isoformat()
            result["chunks_retrieved"] = len(retrieved_chunks)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            raise
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session."""
        return self.conversations.get(session_id, [])
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session."""
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"Cleared conversation for session {session_id}")
    
    def _add_to_history(self, session_id: str, role: str, content: str):
        """Add message to conversation history."""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })


# Global instance
chat_service = ChatService()
