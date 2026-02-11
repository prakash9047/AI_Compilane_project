"""
Streamlit Dashboard - Single Page UI for AI Compliance Engine
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="AI Compliance Engine",
    page_icon="🏛️",
    layout="wide"
)

# Header
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
    st.header("⚖️ Step 2: Run Validation")
    
    doc_id = st.number_input(
        "Document ID",
        min_value=1,
        value=st.session_state.get('last_doc_id', 1),
        help="Enter the document ID to validate"
    )
    
    framework = st.selectbox(
        "Regulatory Framework",
        ["ind_as", "sebi", "rbi", "companies_act"],
        format_func=lambda x: {
            "ind_as": "Ind AS (Indian Accounting Standards)",
            "sebi": "SEBI Regulations",
            "rbi": "RBI Guidelines",
            "companies_act": "Companies Act"
        }[x]
    )
    
    if st.button("🔍 Run Compliance Validation", type="primary"):
        with st.spinner("Running AI validation... This may take 2-3 minutes"):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/validation/{doc_id}/validate",
                    params={"framework": framework}
                )
                if response.status_code == 200:
                    st.success("✅ Validation started! Results will appear below.")
                    st.session_state['validated_doc'] = doc_id
                    st.session_state['validated_framework'] = framework
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
    
    try:
        response = requests.get(f"{API_BASE_URL}/validation/{result_doc_id}/summary")
        if response.status_code == 200:
            summary = response.json()
            
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
            
        else:
            st.info("No validation results yet. Run validation first.")
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
                    st.success("✅ Report generated!")
                    
                    # Download link
                    download_response = requests.get(
                        f"{API_BASE_URL}/reports/{report_doc_id}/download/{report_format}",
                        stream=True
                    )
                    if download_response.status_code == 200:
                        st.download_button(
                            label=f"⬇️ Download {report_format.upper()} Report",
                            data=download_response.content,
                            file_name=f"compliance_report_{report_doc_id}.{report_format}",
                            mime=f"application/{report_format}"
                        )
                else:
                    st.error(f"❌ Report generation failed: {response.text}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    st.subheader("🔍 Semantic Search")
    
    search_query = st.text_input(
        "Ask a question about your documents",
        placeholder="e.g., What is the revenue recognition policy?"
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
# BOTTOM: DETAILED RESULTS TABLE
# ============================================
st.markdown("---")
st.header("📋 Detailed Validation Results")

if st.session_state.get('validated_doc'):
    try:
        response = requests.get(f"{API_BASE_URL}/validation/{st.session_state['validated_doc']}/results")
        if response.status_code == 200:
            results = response.json()
            if results:
                df = pd.DataFrame(results)
                
                # Filter options
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
                
                # Apply filters
                if status_filter and 'status' in df.columns:
                    df = df[df['status'].isin(status_filter)]
                if severity_filter and 'severity' in df.columns:
                    df = df[df['severity'].isin(severity_filter)]
                
                # Display table
                st.dataframe(
                    df[['rule_name', 'status', 'severity', 'confidence_score', 'finding_summary']],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Detailed view
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
