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

# Create three columns for the main workflow
col1, col2, col3 = st.columns(3)

# ============================================
# COLUMN 1: UPLOAD & DOCUMENTS
# ============================================
with col1:
    st.header("📤 Step 1: Upload Document")
    
    uploaded_file = st.file_uploader(
        "Upload financial document",
        type=["pdf", "docx", "xlsx", "png", "jpg", "jpeg"],
        help="Upload PDF, Word, Excel, or Image files"
    )
    
    if uploaded_file:
        if st.button("🚀 Upload & Process", type="primary"):
            with st.spinner("Uploading and processing..."):
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                try:
                    response = requests.post(f"{API_BASE_URL}/documents/upload", files=files)
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Document uploaded! ID: {result['id']}")
                        st.session_state['last_doc_id'] = result['id']
                    else:
                        st.error(f"❌ Upload failed: {response.text}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    st.subheader("📚 Recent Documents")
    
    try:
        response = requests.get(f"{API_BASE_URL}/documents/")
        if response.status_code == 200:
            documents = response.json()
            if documents:
                for doc in documents[:5]:  # Show last 5
                    with st.expander(f"📄 {doc['filename'][:30]}..."):
                        st.write(f"**ID:** {doc['id']}")
                        st.write(f"**Status:** {doc['status']}")
                        st.write(f"**Uploaded:** {doc['created_at'][:19]}")
                        if st.button(f"Use Doc {doc['id']}", key=f"use_{doc['id']}"):
                            st.session_state['last_doc_id'] = doc['id']
                            st.rerun()
            else:
                st.info("No documents uploaded yet")
    except:
        st.warning("⚠️ Cannot connect to backend")

# ============================================
# COLUMN 2: VALIDATION
# ============================================
with col2:
    # Validation section
    st.subheader("⚖️ Step 2: Run Validation")
    
    col1, col2 = st.columns(2)
    with col1:
        doc_id = st.number_input("Document ID", min_value=1, value=1, step=1)
    with col2:
        framework = st.selectbox(
            "Regulatory Framework",
            ["ind_as", "sebi", "rbi"],
            format_func=lambda x: {
                "ind_as": "Ind AS (Indian Accounting Standards)",
                "sebi": "SEBI Regulations",
                "rbi": "RBI Guidelines"
            }[x]
        )
    
    # Check if document exists before allowing validation
    try:
        doc_check = requests.get(f"{API_BASE_URL}/documents/{doc_id}")
        doc_exists = doc_check.status_code == 200
    except:
        doc_exists = False
    
    if st.button("🔍 Run Compliance Validation", disabled=not doc_exists):
        if not doc_exists:
            st.error("❌ Please upload a document first!")
        else:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/validation/{doc_id}/validate",
                    params={"framework": framework}
                )
                if response.status_code == 200:
                    st.session_state['validated_doc'] = doc_id
                    st.session_state['validated_framework'] = framework
                    st.session_state['validation_start_time'] = time.time()
                    st.session_state['validation_running'] = True
                    # Immediately rerun to show polling UI
                    st.rerun()
                else:
                    st.error(f"❌ Validation failed: {response.text}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    st.subheader("📊 Validation Results")
    
    if st.button("🔄 Refresh Results"):
        st.rerun()
    
    # Show results if available
    result_doc_id = st.session_state.get('validated_doc', doc_id)
    
    # Check if validation is currently running
    if st.session_state.get('validation_running', False):
        # Validation in progress - show polling UI
        st.info("⏳ **Validation in Progress**")
        st.write("AI is analyzing your document against compliance rules...")
        st.write("This typically takes 2-3 minutes. The page will auto-refresh when complete.")
        
        # Add stop button
        if st.button("🛑 Stop Validation", key="stop_validation"):
            st.session_state['validation_running'] = False
            st.warning("⚠️ Validation cancelled by user")
            st.stop()
        
        # Show progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Poll for results (max 3 minutes)
        max_wait = 180  # 3 minutes
        poll_interval = 10  # 10 seconds
        start_time = st.session_state.get('validation_start_time', time.time())
        
        for elapsed in range(0, max_wait, poll_interval):
            # Check if user stopped validation
            if not st.session_state.get('validation_running', True):
                st.warning("⚠️ Validation stopped")
                break
            
            # Check for results
            check_response = requests.get(f"{API_BASE_URL}/validation/{result_doc_id}/summary")
            if check_response.status_code == 200:
                check_summary = check_response.json()
                if check_summary.get('total_rules', 0) > 0:
                    # Results ready!
                    st.session_state['validation_running'] = False
                    st.success("✅ Validation complete! Displaying results...")
                    time.sleep(0.5)
                    st.rerun()
                    break
            
            # Update progress
            progress = min(elapsed / max_wait, 0.95)
            progress_bar.progress(progress)
            status_text.text(f"⏳ Analyzing... {elapsed}s elapsed (typically takes 2-3 minutes)")
            time.sleep(poll_interval)
        
        # If we get here, validation took too long or was stopped
        if st.session_state.get('validation_running', True):
            st.warning("⚠️ Validation is taking longer than expected. Click 'Refresh Results' to check status.")
            st.session_state['validation_running'] = False
    
    else:
        # Not currently validating - check for existing results
        try:
            response = requests.get(f"{API_BASE_URL}/validation/{result_doc_id}/summary")
            if response.status_code == 200:
                summary = response.json()
                total_rules = summary.get('total_rules', 0)
                
                if total_rules > 0:
                    # Display metrics
                    metric_cols = st.columns(2)
                    with metric_cols[0]:
                        st.metric("Compliance Score", f"{summary.get('compliance_score', 0):.1f}%")
                        st.metric("Rules Passed", summary.get('rules_passed', 0))
                    with metric_cols[1]:
                        st.metric("Total Rules", summary.get('total_rules', 0))
                        st.metric("Rules Failed", summary.get('rules_failed', 0))
                    
                    # Show issues by severity
                    if summary.get('critical_issues', 0) > 0:
                        st.error(f"🔴 Critical Issues: {summary['critical_issues']}")
                    if summary.get('high_issues', 0) > 0:
                        st.warning(f"🟠 High Issues: {summary['high_issues']}")
                    if summary.get('medium_issues', 0) > 0:
                        st.info(f"🟡 Medium Issues: {summary['medium_issues']}")
                
                    # Visualizations
                    st.markdown("---")
                    st.subheader("📊 Visual Analytics")
                    
                    # Compliance Gauge
                    gauge_fig = create_compliance_gauge(
                        summary.get('compliance_score', 0),
                        "Compliance Score"
                    )
                    st.plotly_chart(gauge_fig, use_container_width=True)
                    
                    # Severity Distribution
                    severity_counts = {
                        'Critical': summary.get('critical_issues', 0),
                        'High': summary.get('high_issues', 0),
                        'Medium': summary.get('medium_issues', 0),
                        'Low': summary.get('low_issues', 0)
                    }
                    
                    severity_counts = {k: v for k, v in severity_counts.items() if v > 0}
                    
                    if severity_counts:
                        st.subheader("Issue Severity Breakdown")
                        pie_fig = create_severity_pie_chart(severity_counts)
                        st.plotly_chart(pie_fig, use_container_width=True)
                    else:
                        st.success("🎉 No issues found - 100% compliant!")
                else:
                    st.info("No validation results yet. Run validation first.")
            else:
                st.info("No validation results available")
        except:
            st.info("No validation results available")

# ============================================
# COLUMN 3: REPORTS & SEARCH
# ============================================
with col3:
    st.header("📈 Step 3: Generate Report")
    
    report_doc_id = st.number_input(
        "Document ID for Report",
        min_value=1,
        value=st.session_state.get('validated_doc', 1),
        help="Enter document ID"
    )
    
    report_type = st.selectbox(
        "Report Type",
        ["full", "summary", "gap_analysis"],
        format_func=lambda x: {
            "full": "Full Report (All Rules)",
            "summary": "Summary Report (Overview)",
            "gap_analysis": "Gap Analysis (Issues Only)"
        }[x]
    )
    
    report_format = st.selectbox(
        "Format",
        ["pdf", "excel", "json"],
        format_func=lambda x: x.upper()
    )
    
    if st.button("📄 Generate Report", type="primary"):
        with st.spinner("Generating report..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/reports/{report_doc_id}/generate",
                    params={"report_type": report_type}
                )
                if response.status_code == 200:
                    result = response.json()
                    report_id = result.get('report_id')
                    
                    if report_id:
                        st.success(f"✅ Report generated! (Report ID: {report_id})")
                        
                        # Download link using correct report_id
                        download_response = requests.get(
                            f"{API_BASE_URL}/reports/{report_id}/download/{report_format}",
                            stream=True
                        )
                        if download_response.status_code == 200:
                            st.download_button(
                                label=f"⬇️ Download {report_format.upper()} Report",
                                data=download_response.content,
                                file_name=f"compliance_report_{report_id}.{report_format}",
                                mime="application/pdf" if report_format == "pdf" else f"application/{report_format}",
                                type="primary"
                            )
                        else:
                            st.error(f"❌ Download failed: {download_response.text}")
                    else:
                        st.warning("⚠️ Report generated but no report ID returned")
                else:
                    st.error(f"❌ Report generation failed: {response.text}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    st.subheader("🔍 Semantic Search")
    
    # Example questions
    with st.expander("💡 Example Questions"):
        st.markdown("""
        **Financial Reporting Questions:**
        - What are the revenue recognition policies?
        - How are financial instruments classified?
        - What is the depreciation method for property, plant and equipment?
        
        **Compliance Questions:**
        - Are related party transactions disclosed?
        - What are the contingent liabilities?
        - How are employee benefits accounted for?
        
        **Risk & Governance:**
        - What are the key accounting estimates and judgments?
        - Are there any post-balance sheet events?
        - What is the going concern assessment?
        
        **Specific Standards:**
        - How does the company comply with IND AS 115 (Revenue)?
        - What are the lease accounting policies under IND AS 116?
        - How are deferred taxes calculated per IND AS 12?
        """)
    
    search_query = st.text_input(
        "Enter your question",
        placeholder="e.g., What are the revenue recognition policies?"
    )
    
    if st.button("🔎 Search"):
        if search_query:
            with st.spinner("Searching..."):
                try:
                    response = requests.get(
                        f"{API_BASE_URL}/search/",
                        params={"query": search_query, "n_results": 5}
                    )
                    if response.status_code == 200:
                        results = response.json()
                        if results.get('results'):
                            st.success(f"Found {len(results['results'])} results")
                            for i, result in enumerate(results['results'], 1):
                                with st.expander(f"Result {i} (Score: {result.get('score', 0):.2f})"):
                                    st.write(result.get('text', ''))
                                    st.caption(f"Document ID: {result.get('document_id', 'N/A')}")
                        else:
                            st.info("No results found")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================
# FULL-WIDTH VISUALIZATION SECTION
# ============================================
st.markdown("---")

if st.session_state.get('validated_doc'):
    st.header("📊 Detailed Visual Analytics")
    
    try:
        response = requests.get(f"{API_BASE_URL}/validation/{st.session_state['validated_doc']}/results")
        summary_response = requests.get(f"{API_BASE_URL}/validation/{st.session_state['validated_doc']}/summary")
        
        if response.status_code == 200 and summary_response.status_code == 200:
            results = response.json()
            summary = summary_response.json()
            
            if results:
                viz_tabs = st.tabs(["📋 Rule Analysis", "🎯 Framework Comparison", "📄 Data Table"])
                
                with viz_tabs[0]:
                    st.subheader("Top Failed Rules")
                    df_results = pd.DataFrame(results)
                    failed_rules = df_results[df_results['status'] != 'compliant']
                    
                    if not failed_rules.empty:
                        rule_counts = failed_rules['rule_name'].value_counts().reset_index()
                        rule_counts.columns = ['rule_name', 'fail_count']
                        rule_data = rule_counts.to_dict('records')
                        
                        rule_fig = create_rule_compliance_breakdown(rule_data)
                        st.plotly_chart(rule_fig, use_container_width=True)
                    else:
                        st.success("🎉 All rules passed! No failures to display.")
                
                with viz_tabs[1]:
                    if 'framework' in df_results.columns:
                        st.subheader("Compliance by Framework")
                        framework_stats = {}
                        for framework in df_results['framework'].unique():
                            fw_data = df_results[df_results['framework'] == framework]
                            framework_stats[framework] = {
                                'passed': len(fw_data[fw_data['status'] == 'compliant']),
                                'failed': len(fw_data[fw_data['status'] != 'compliant'])
                            }
                        
                        if len(framework_stats) > 0:
                            fw_fig = create_framework_comparison(framework_stats)
                            st.plotly_chart(fw_fig, use_container_width=True)
                        else:
                            st.info("Run validation to see framework comparison")
                    else:
                        st.info("Run validation to see framework comparison")
                
                with viz_tabs[2]:
                    st.subheader("Detailed Results Table")
                    df = pd.DataFrame(results)
                    
                    filter_col1, filter_col2 = st.columns(2)
                    with filter_col1:
                        status_filter = st.multiselect(
                            "Filter by Status",
                            options=df['status'].unique() if 'status' in df.columns else [],
                            default=df['status'].unique() if 'status' in df.columns else []
                        )
                    with filter_col2:
                        severity_filter = st.multiselect(
                            "Filter by Severity",
                            options=df['severity'].unique() if 'severity' in df.columns else [],
                            default=df['severity'].unique() if 'severity' in df.columns else []
                        )
                
                if status_filter and 'status' in df.columns:
                    df = df[df['status'].isin(status_filter)]
                if severity_filter and 'severity' in df.columns:
                    df = df[df['severity'].isin(severity_filter)]
                
                st.dataframe(
                    df[['rule_name', 'status', 'severity', 'confidence_score', 'finding_summary']],
                    use_container_width=True,
                    hide_index=True
                )
                
                if st.checkbox("Show Detailed Findings"):
                    for idx, row in df.iterrows():
                        with st.expander(f"{row['rule_name']} - {row['status']}"):
                            st.write(f"**Status:** {row['status']}")
                            st.write(f"**Severity:** {row['severity']}")
                            st.write(f"**Confidence:** {row.get('confidence_score', 0):.1%}")
                            st.write(f"**Finding:** {row['finding_summary']}")
                            if row.get('ai_explanation'):
                                st.info(f"**AI Explanation:** {row['ai_explanation']}")
                            if row.get('remediation_suggestions'):
                                st.warning(f"**Remediation:** {row['remediation_suggestions']}")
            else:
                st.info("No detailed results available yet")
    except Exception as e:
        st.error(f"Error loading results: {str(e)}")
else:
    st.info("👆 Upload a document and run validation to see detailed results here")

# Footer
st.markdown("---")
st.caption("🏛️ AI Compliance Engine | Powered by GPT-4 & ChromaDB")
