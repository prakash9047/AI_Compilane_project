"""
Unified Streamlit Application with Embedded FastAPI Backend
This file combines the FastAPI backend and Streamlit frontend into a single deployable app.
"""
import streamlit as st

# ============================================
# STREAMLIT CONFIGURATION (MUST BE FIRST!)
# ============================================

st.set_page_config(
    page_title="AI Compliance Engine",
    page_icon="🏛️",
    layout="wide"
)

# ============================================
# LOAD ENVIRONMENT VARIABLES
# ============================================

import os
from pathlib import Path

# Try to load from Streamlit secrets first (for cloud deployment)
try:
    # Streamlit Cloud deployment - use secrets
    os.environ["OPENAI_API_KEY"] = st.secrets.get("OPENAI_API_KEY", "")
    os.environ["LLM_PROVIDER"] = st.secrets.get("LLM_PROVIDER", "openai")
    os.environ["LLM_MODEL"] = st.secrets.get("LLM_MODEL", "gpt-4o-mini")
    os.environ["ENVIRONMENT"] = st.secrets.get("ENVIRONMENT", "production")
except:
    # Local development - use .env file
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path, override=True)

# Verify API key is loaded
if not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ OPENAI_API_KEY not found. Please configure it in Streamlit secrets or .env file.")
    st.info("**For Streamlit Cloud**: Add OPENAI_API_KEY in App Settings → Secrets")
    st.info("**For Local**: Add OPENAI_API_KEY in .env file")
    st.stop()

# Now import other modules
import requests
import pandas as pd
import json
import threading
import time
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Import FastAPI app and dependencies
from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager

# Import chart components
from frontend.components.charts import (
    create_compliance_gauge,
    create_severity_pie_chart,
    create_severity_bar_chart,
    create_rule_compliance_breakdown,
    create_framework_comparison
)

# ============================================
# BACKEND INITIALIZATION
# ============================================

@st.cache_resource
def start_backend():
    """Start FastAPI backend in a background thread."""
    from app.main import app as fastapi_app
    
    def run_server():
        uvicorn.run(
            fastapi_app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
    
    # Start backend thread
    backend_thread = threading.Thread(target=run_server, daemon=True)
    backend_thread.start()
    
    # Wait for backend to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=1)
            if response.status_code == 200:
                return True
        except:
            time.sleep(1)
    
    return False

# Initialize backend
with st.spinner("🚀 Starting AI Compliance Engine..."):
    backend_ready = start_backend()
    if not backend_ready:
        st.error("❌ Failed to start backend server. Please refresh the page.")
        st.stop()

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000/api/v1"

# ============================================
# HEADER
# ============================================

st.title("🏛️ AI Compliance Engine")
st.markdown("### Enterprise Document Compliance Validation System")
st.markdown("---")

# Create two main columns layout
left_col, right_col = st.columns([1, 2], gap="large")

# ============================================
# LEFT COLUMN: UPLOAD & HISTORY
# ============================================
with left_col:
    st.header("1️⃣ Upload Document")
    
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Upload financial document",
            type=["pdf", "docx", "xlsx", "png", "jpg", "jpeg"],
            help="Upload PDF, Word, Excel, or Image files"
        )
        
        if uploaded_file:
            if st.button("🚀 Upload & Process", type="primary", use_container_width=True):
                with st.spinner("Uploading and processing..."):
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    try:
                        response = requests.post(f"{API_BASE_URL}/documents/upload", files=files)
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ Document uploaded! ID: {result['id']}")
                            st.session_state['last_doc_id'] = result['id']
                            st.rerun()
                        else:
                            st.error(f"❌ Upload failed: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    st.subheader("📚 Recent Documents")
    
    try:
        response = requests.get(f"{API_BASE_URL}/documents/")
        if response.status_code == 200:
            documents = response.json()
            if documents:
                for doc in documents[:5]:  # Show last 5
                    with st.expander(f"📄 {doc['filename'][:30]}..."):
                        col_a, col_b = st.columns(2)
                        col_a.caption(f"ID: {doc['id']}")
                        col_b.caption(f"{doc['status']}")
                        st.caption(f"📅 {doc['created_at'][:10]}")
                        
                        if st.button(f"Analyze Doc {doc['id']}", key=f"use_{doc['id']}", use_container_width=True):
                            st.session_state['last_doc_id'] = doc['id']
                            st.session_state['validated_doc'] = doc['id']
                            st.rerun()
            else:
                st.info("No documents uploaded yet")
    except:
        st.warning("⚠️ Cannot connect to backend")

# ============================================
# RIGHT COLUMN: ANALYSIS TABS
# ============================================
with right_col:
    # Initialize tabs
    tab_validation, tab_reports, tab_chat = st.tabs([
        "⚖️ Compliance Validation", 
        "📑 Report Generation", 
        "💬 AI Assistant"
    ])
    
    # -------------------------------------------------------------
    # TAB 1: VALIDATION
    # -------------------------------------------------------------
    with tab_validation:
        st.header("2️⃣ Run Validation")
        
        # Validation Controls
        with st.container(border=True):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                # Default to last uploaded/selected doc
                default_id = st.session_state.get('last_doc_id', 1)
                doc_id = st.number_input("Document ID", min_value=1, value=default_id, step=1, key="val_doc_id")
            with col_v2:
                framework = st.selectbox(
                    "Regulatory Framework",
                    ["ind_as", "sebi", "rbi"],
                    format_func=lambda x: {
                        "ind_as": "Ind AS (Indian Accounting Standards)",
                        "sebi": "SEBI Regulations",
                        "rbi": "RBI Guidelines"
                    }[x]
                )
            
            if st.button("🔍 Run Compliance Check", type="primary", use_container_width=True):
                try:
                    # Check doc exists first
                    doc_check = requests.get(f"{API_BASE_URL}/documents/{doc_id}")
                    if doc_check.status_code == 200:
                        response = requests.post(
                            f"{API_BASE_URL}/validation/{doc_id}/validate",
                            params={"framework": framework}
                        )
                        if response.status_code == 200:
                            st.session_state['validated_doc'] = doc_id
                            st.session_state['validated_framework'] = framework
                            st.session_state['validation_start_time'] = time.time()
                            st.session_state['validation_running'] = True
                            st.rerun()
                        else:
                            st.error(f"❌ Validation failed: {response.text}")
                    else:
                        st.error("❌ Document not found")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        # Validation Progress / Results
        if st.session_state.get('validation_running', False):
            st.info("⏳ **Validation in Progress**")
            st.write("AI is analyzing your document against compliance rules...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            max_wait = 180
            start_time = st.session_state.get('validation_start_time', time.time())
            
            # Polling logic
            for elapsed in range(0, max_wait, 5):
                if not st.session_state.get('validation_running'): break
                
                check_res = requests.get(f"{API_BASE_URL}/validation/{doc_id}/summary")
                if check_res.status_code == 200 and check_res.json().get('total_rules', 0) > 0:
                    st.session_state['validation_running'] = False
                    st.success("✅ Validation Complete!")
                    st.rerun()
                    break
                
                progress = min(elapsed / max_wait, 0.95)
                progress_bar.progress(progress)
                status_text.text(f"Analyzing... {elapsed}s elapsed")
                time.sleep(5)
            
            if st.session_state.get('validation_running'):
                st.warning("⚠️ Validation taking longer than expected. Refresh to check.")
                st.session_state['validation_running'] = False

        # Display Results
        result_id = st.session_state.get('validated_doc', doc_id)
        if result_id:
            try:
                summary_res = requests.get(f"{API_BASE_URL}/validation/{result_id}/summary")
                results_res = requests.get(f"{API_BASE_URL}/validation/{result_id}/results")
                
                if summary_res.status_code == 200 and results_res.status_code == 200:
                    summary = summary_res.json()
                    results = results_res.json()
                    
                    if summary['total_rules'] > 0:
                        st.divider()
                        st.subheader(f"📊 Results for Doc {result_id}")
                        
                        # Metrics Row
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Compliance Score", f"{summary.get('compliance_score', 0):.1f}%")
                        m2.metric("Rules Passed", summary.get('rules_passed', 0))
                        m3.metric("Critical Issues", summary.get('critical_issues', 0))
                        m4.metric("High Issues", summary.get('high_issues', 0))
                        
                        # Charts
                        c1, c2 = st.columns(2)
                        with c1:
                            gauge_fig = create_compliance_gauge(summary.get('compliance_score', 0), "Compliance Score")
                            st.plotly_chart(gauge_fig, use_container_width=True)
                        with c2:
                            counts = {
                                'Critical': summary.get('critical_issues', 0),
                                'High': summary.get('high_issues', 0),
                                'Medium': summary.get('medium_issues', 0)
                            }
                            if sum(counts.values()) > 0:
                                pie_fig = create_severity_pie_chart(counts)
                                st.plotly_chart(pie_fig, use_container_width=True)
                            else:
                                st.success("No issues found! 🎉")
                        
                        # Detailed Findings
                        with st.expander("📝 View Detailed Findings"):
                            df = pd.DataFrame(results)
                            st.dataframe(
                                df[['rule_name', 'status', 'severity', 'finding_summary']], 
                                use_container_width=True, hide_index=True
                            )
                    else:
                        st.info("Run validation to see results.")
            except:
                pass

    # -------------------------------------------------------------
    # TAB 2: REPORTS
    # -------------------------------------------------------------
    with tab_reports:
        st.header("3️⃣ Generate Report")
        
        with st.container(border=True):
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                 rep_doc_id = st.number_input("Document ID", min_value=1, value=st.session_state.get('last_doc_id', 1), key="rep_doc_id")
            with col_r2:
                rep_type = st.selectbox("Report Type", ["full", "summary", "gap_analysis"], format_func=lambda x: x.replace("_", " ").title())
            
            fmt_col, btn_col = st.columns([1, 1])
            with fmt_col:
                rep_fmt = st.selectbox("Format", ["pdf", "excel", "json"], format_func=str.upper)
            with btn_col:
                st.write("") # Spacer
                if st.button("📄 Generate Report", type="primary", use_container_width=True, key="gen_rep_btn"):
                    with st.spinner("Generating..."):
                        try:
                            # Generate
                            gen_res = requests.post(
                                f"{API_BASE_URL}/reports/{rep_doc_id}/generate",
                                params={"report_type": rep_type}
                            )
                            if gen_res.status_code == 200:
                                report_data = gen_res.json()
                                report_id = report_data.get('report_id')
                                if report_id:
                                    st.success(f"✅ Report Ready! (ID: {report_id})")
                                    # Download Button
                                    dl_res = requests.get(f"{API_BASE_URL}/reports/{report_id}/download/{rep_fmt}")
                                    if dl_res.status_code == 200:
                                        st.download_button(
                                            label=f"⬇️ Download {rep_fmt.upper()}",
                                            data=dl_res.content,
                                            file_name=f"compliance_report_{report_id}.{rep_fmt}",
                                            mime="application/pdf" if rep_fmt == "pdf" else "application/octet-stream",
                                            type="primary",
                                            use_container_width=True
                                        )
                            else:
                                st.error(f"Failed: {gen_res.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")

    # -------------------------------------------------------------
    # TAB 3: AI CHAT
    # -------------------------------------------------------------
    with tab_chat:
        st.header("4️⃣ AI Chat Assistant")
        
        # Document Context Selection
        with st.container(border=True):
            col_c1, col_c2 = st.columns([1, 3])
            with col_c1:
                chat_doc_id = st.number_input(
                    "Chat Context (Doc ID)", 
                    min_value=1, 
                    value=st.session_state.get('last_doc_id', 1),
                    help="ID of document to chat about"
                )
            with col_c2:
                st.info(f"💬 Chatting about Document ID: **{chat_doc_id}**")
        
        # Chat History
        chat_container = st.container(height=400)
        
        # Initialize session
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "session_id" not in st.session_state:
            import uuid
            st.session_state.session_id = str(uuid.uuid4())
            
        with chat_container:
            if not st.session_state.messages:
                st.markdown("👋 *I'm your Compliance Assistant. Ask me anything about your document!*")
            
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        # Input - Note: st.chat_input pins to bottom, which is good
        if prompt := st.chat_input("Ask about compliance, financial data, or risks...", key="chat_input"):
            # Update history UI immediately
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            payload = {
                                "question": prompt,
                                "session_id": st.session_state.session_id,
                                "document_id": int(chat_doc_id),
                                "n_results": 5
                            }
                            res = requests.post(f"{API_BASE_URL}/chat/ask", json=payload)
                            
                            if res.status_code == 200:
                                ans = res.json().get("answer", "No response")
                                st.markdown(ans)
                                st.session_state.messages.append({"role": "assistant", "content": ans})
                                
                                # Examples (Semantic Search integrated)
                                sources = res.json().get("sources", [])
                                if sources:
                                    with st.expander("📚 Referenced Sources"):
                                        for s in sources:
                                            st.caption(f"Section: {s.get('metadata', {}).get('title', 'Unknown')}")
                                            st.markdown(f"> {s.get('content', '')[:150]}...")
                            else:
                                err = f"Error: {res.text}"
                                st.error(err)
                                st.session_state.messages.append({"role": "assistant", "content": err})
                        except Exception as e:
                            st.error(f"Connection Error: {e}")

st.markdown("---")
st.caption("🏛️ AI Compliance Engine | Powered by GPT-4 & ChromaDB")
