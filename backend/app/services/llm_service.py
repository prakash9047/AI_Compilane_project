"""
LLM Service for RAG chatbot using OpenAI GPT-4o-mini.
"""
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from loguru import logger

from app.core.config import settings


class LLMService:
    """Service for LLM-based question answering."""
    
    def __init__(self):
        """Initialize LLM service."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set. LLM features will not work.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(f"LLM service initialized with model: {settings.LLM_MODEL}")
    
    async def generate_answer(
        self,
        question: str,
        context_chunks: List[Dict],
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Generate an answer using retrieved context.
        
        Args:
            question: User's question
            context_chunks: Retrieved document chunks from RAG
            conversation_history: Previous messages in conversation
            
        Returns:
            Dict with answer, sources, and metadata
        """
        if not self.client:
            return {
                "answer": "LLM service not configured. Please set OPENAI_API_KEY.",
                "sources": [],
                "model": "none"
            }
        
        try:
            # Build context from retrieved chunks
            context_text = self._build_context(context_chunks)
            
            # Build messages
            messages = self._build_messages(question, context_text, conversation_history)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )
            
            answer = response.choices[0].message.content
            
            # Extract sources
            sources = self._extract_sources(context_chunks)
            
            return {
                "answer": answer,
                "sources": sources,
                "model": settings.LLM_MODEL,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "sources": [],
                "model": settings.LLM_MODEL
            }
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context string from retrieved chunks."""
        if not chunks:
            return "No relevant information found in the documents."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            
            # Add source information
            source_info = f"[Source {i}]"
            if metadata.get("title"):
                source_info += f" {metadata['title']}"
            
            context_parts.append(f"{source_info}\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _build_messages(
        self,
        question: str,
        context: str,
        history: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """Build message list for OpenAI API."""
        
        system_prompt = """You are an AI assistant specialized in compliance and regulatory analysis. 
Your role is to answer questions based on the provided document context.

Guidelines:
- Answer questions accurately based on the provided context
- If the context doesn't contain enough information, say so clearly
- Cite specific sections or sources when possible
- For compliance questions, be precise and reference specific rules or regulations
- If asked about gaps or violations, provide detailed explanations
- Maintain a professional, helpful tone

Always base your answers on the provided context. Do not make up information."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if history:
            for msg in history[-10:]:  # Keep last 10 messages for context
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # Add current question with context
        user_message = f"""Context from documents:
{context}

Question: {question}

Please provide a detailed answer based on the context above."""

        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Extract source information from chunks."""
        sources = []
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            sources.append({
                "document_id": metadata.get("document_id"),
                "title": metadata.get("title", "Unknown"),
                "type": metadata.get("type", "unknown"),
                "content_preview": chunk.get("content", "")[:200] + "..."
            })
        return sources


# Global instance
llm_service = LLMService()
