"""
Chat Page - RAG-based Q&A Interface
"""
import streamlit as st
import requests
from datetime import datetime
import uuid

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="Compliance Chat",
    page_icon="💬",
    layout="wide"
)

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Header
st.title("💬 Compliance Chatbot")
st.markdown("### Ask questions about your compliance documents")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Chat Settings")
    
    st.write(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
    
    n_results = st.slider(
        "Context Chunks",
        min_value=3,
        max_value=10,
        value=5,
        help="Number of document chunks to retrieve"
    )
    
    document_filter = st.number_input(
        "Filter by Document ID (optional)",
        min_value=0,
        value=0,
        help="Leave as 0 to search all documents"
    )
    
    if st.button("🗑️ Clear Conversation"):
        try:
            response = requests.delete(f"{API_BASE_URL}/chat/clear/{st.session_state.session_id}")
            if response.status_code == 200:
                st.session_state.messages = []
                st.success("Conversation cleared!")
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    
    if st.button("🔄 New Session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.subheader("📊 Example Questions")
    st.markdown("""
    - What are the revenue recognition policies?
    - Are there any compliance gaps in the financial statements?
    - Summarize the auditor's report
    - What are the key accounting policies?
    - Explain the notes to accounts
    """)

# Main chat interface
chat_container = st.container()

# Display chat messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show sources for assistant messages
            if message["role"] == "assistant" and "sources" in message:
                if message["sources"]:
                    with st.expander("📚 Sources"):
                        for i, source in enumerate(message["sources"], 1):
                            st.caption(f"**Source {i}:** Doc ID {source.get('document_id')} - {source.get('title', 'Unknown')}")
                            st.text(source.get('content_preview', ''))

# Chat input
if prompt := st.chat_input("Ask a question about your compliance documents..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 Thinking...")
        
        try:
            # Call chat API
            response = requests.post(
                f"{API_BASE_URL}/chat/ask",
                json={
                    "question": prompt,
                    "session_id": st.session_state.session_id,
                    "document_id": document_filter if document_filter > 0 else None,
                    "n_results": n_results
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "No answer generated")
                sources = result.get("sources", [])
                
                # Display answer
                message_placeholder.markdown(answer)
                
                # Display sources
                if sources:
                    with st.expander("📚 Sources"):
                        for i, source in enumerate(sources, 1):
                            st.caption(f"**Source {i}:** Doc ID {source.get('document_id')} - {source.get('title', 'Unknown')}")
                            st.text(source.get('content_preview', ''))
                
                # Add to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
                
                # Show metadata
                st.caption(f"🤖 Model: {result.get('model', 'unknown')} | 📊 Chunks: {result.get('chunks_retrieved', 0)} | 🎫 Tokens: {result.get('tokens_used', 0)}")
                
            else:
                error_msg = f"❌ Error: {response.text}"
                message_placeholder.markdown(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
                
        except Exception as e:
            error_msg = f"❌ Connection error: {str(e)}"
            message_placeholder.markdown(error_msg)
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg
            })

# Footer
st.markdown("---")
st.caption("💬 RAG-powered Compliance Chatbot | GPT-4o-mini + ChromaDB")
