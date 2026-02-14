# AI Compliance Engine 🤖⚖️

An AI-powered compliance validation system for financial documents using OpenAI GPT-4 and RAG (Retrieval-Augmented Generation).

## 🌟 Features

- **📄 Document Upload** - Support for PDF, DOCX, and Markdown files
- **🤖 AI-Powered Validation** - Automated compliance checking against IND AS, SEBI, and RBI regulations
- **📊 Visual Analytics** - Interactive charts and compliance dashboards
- **📑 PDF Report Generation** - Professional compliance reports with detailed findings
- **🔍 Semantic Search** - Natural language search across documents
- **💬 AI Chat** - Ask questions about your documents

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API Key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/prakash9047/AI_Compilane_project.git
cd AI_Compilane_project
```

2. **Create virtual environment**
```bash
python -m venv env
env\Scripts\activate  # Windows
# source env/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements_unified.txt
```

4. **Set up environment variables**
Create a `.env` file:
```env
OPENAI_API_KEY=your-openai-api-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

5. **Run the application**
```bash
streamlit run app_unified.py
```

The app will be available at `http://localhost:8501`

## 📁 Project Structure

```
compliance-ai-engine/
├── app_unified.py              # Main Streamlit application
├── backend/
│   ├── app/
│   │   ├── api/                # FastAPI endpoints
│   │   ├── engines/            # Core processing engines
│   │   │   ├── compliance/     # Compliance validation
│   │   │   ├── extraction/     # Document extraction
│   │   │   ├── rag/           # RAG pipeline
│   │   │   └── segmentation/   # Document segmentation
│   │   ├── db/                 # Database models
│   │   └── workers/            # Background tasks
│   └── data/
│       └── compliance_rules/   # Regulatory rules (IND AS, SEBI, RBI)
├── requirements_unified.txt    # Python dependencies
└── .env                        # Environment variables (not in Git)
```

## 🎯 Usage

### 1. Upload Document
- Click "Browse files" and upload a PDF, DOCX, or MD file
- Document will be processed and indexed

### 2. Run Validation
- Enter document ID
- Select regulatory framework (IND AS, SEBI, RBI)
- Click "Run Compliance Validation"
- Wait 2-3 minutes for AI analysis

### 3. View Results
- Compliance score and metrics
- Visual analytics with charts
- Detailed findings by rule

### 4. Generate Report
- Select document ID
- Choose report type (Full, Summary, Gap Analysis)
- Select format (PDF, Excel, JSON)
- Download professional compliance report

### 5. Semantic Search
- Ask questions about your documents
- Get AI-powered answers with citations

## 🔧 Technology Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **AI/ML**: OpenAI GPT-4o-mini, LangChain
- **Database**: SQLite (SQLAlchemy ORM)
- **Vector Store**: ChromaDB
- **PDF Generation**: ReportLab
- **Charts**: Plotly

## 📊 Supported Frameworks

- **IND AS** - Indian Accounting Standards (20 rules)
- **SEBI** - Securities and Exchange Board of India
- **RBI** - Reserve Bank of India Guidelines

## 🛠️ Configuration

Key environment variables in `.env`:

```env
# AI Configuration
OPENAI_API_KEY=your-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Paths
COMPLIANCE_RULES_PATH=./backend/data/compliance_rules

# Database
DATABASE_URL=sqlite+aiosqlite:///./backend/data/compliance.db
```

## 📝 Example Questions for Semantic Search

**Financial Reporting:**
- What are the revenue recognition policies?
- How are financial instruments classified?

**Compliance:**
- Are related party transactions disclosed?
- What are the contingent liabilities?

**Specific Standards:**
- How does the company comply with IND AS 115?
- What are the lease accounting policies under IND AS 116?

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Author

**Prakash**
- GitHub: [@prakash9047](https://github.com/prakash9047)

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Streamlit for the amazing framework
- LangChain for RAG capabilities

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Made with ❤️ for better compliance management**
