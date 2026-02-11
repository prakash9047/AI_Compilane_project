# 🏛️ AI Compliance Engine - Simplified Setup

Enterprise-grade AI system for extracting, validating, and generating compliance reports from multi-format documents against Indian regulatory frameworks (Ind AS, SEBI, RBI).

## ✨ Features

- **Multi-Format Document Processing**: PDF (digital & scanned), DOCX, XLSX, images with OCR
- **Intelligent Segmentation**: Hierarchical document structure analysis
- **AI-Powered Compliance Validation**: LLM-based validation against Indian regulatory frameworks
- **RAG-Powered Search**: Semantic search across indexed documents
- **Comprehensive Reporting**: PDF, Excel, JSON export with visualizations
- **Simplified Deployment**: SQLite database, no external dependencies required

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Tesseract OCR (for scanned documents)

### Installation

1. **Clone and setup**:
```bash
cd compliance-ai-engine

# Create virtual environment
python -m venv env

# Activate (Windows)
env\Scripts\activate

# Activate (Linux/Mac)
source env/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and add your API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY)
```

4. **Install Tesseract OCR**:

**Windows**:
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install and note the installation path
- Update `TESSERACT_PATH` in `.env`

**Linux**:
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin
```

**Mac**:
```bash
brew install tesseract tesseract-lang
```

5. **Start the backend**:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Start the frontend** (in a new terminal):
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

## 📖 Access Points

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend Dashboard**: http://localhost:8501

## 🎯 Usage Example

### 1. Upload Document
```python
import requests

files = {"file": open("financial_statement.pdf", "rb")}
response = requests.post("http://localhost:8000/api/v1/documents/upload", files=files)
document_id = response.json()["id"]
```

### 2. Run Compliance Validation
```python
response = requests.post(
    f"http://localhost:8000/api/v1/validation/{document_id}/validate",
    params={"framework": "ind_as"}
)
```

### 3. Get Validation Results
```python
response = requests.get(f"http://localhost:8000/api/v1/validation/{document_id}/summary")
summary = response.json()
print(f"Compliance Score: {summary['compliance_score']}%")
```

### 4. Semantic Search
```python
response = requests.get(
    "http://localhost:8000/api/v1/search/",
    params={"query": "related party transactions", "n_results": 10}
)
results = response.json()
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# AI/ML
OPENAI_API_KEY=your-openai-api-key
LLM_PROVIDER=openai  # or anthropic
LLM_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# OCR
TESSERACT_PATH=/usr/bin/tesseract
OCR_LANGUAGE=eng+hin
OCR_DPI=300

# Database (SQLite - no setup required!)
DATABASE_URL=sqlite+aiosqlite:///./data/compliance.db
```

### Compliance Rules

Add custom compliance rules in `data/compliance_rules/`:

```json
{
  "id": "custom_rule_1",
  "framework": "ind_as",
  "name": "Custom Disclosure Requirement",
  "description": "Description of the requirement",
  "requirements": "Specific requirements",
  "keywords": ["keyword1", "keyword2"],
  "severity": "high",
  "mandatory": true
}
```

## 📊 API Endpoints

### Documents
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents/` - List documents
- `GET /api/v1/documents/{id}` - Get document details

### Validation
- `POST /api/v1/validation/{id}/validate` - Run validation
- `GET /api/v1/validation/{id}/results` - Get results
- `GET /api/v1/validation/{id}/summary` - Get summary

### Reports
- `POST /api/v1/reports/{id}/generate` - Generate report
- `GET /api/v1/reports/{id}/reports` - List reports
- `GET /api/v1/reports/{id}/download/{format}` - Download report

### Search
- `GET /api/v1/search/` - Semantic search
- `POST /api/v1/search/ask` - Ask questions

Full API documentation: http://localhost:8000/docs

## 📁 Project Structure

```
compliance-ai-engine/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/      # API routes
│   │   ├── core/                  # Config, security
│   │   ├── db/models/             # Database models
│   │   ├── engines/
│   │   │   ├── extraction/        # Document extraction
│   │   │   ├── segmentation/      # Document segmentation
│   │   │   ├── compliance/        # Validation engine
│   │   │   └── rag/               # RAG pipeline
│   │   ├── vector_store/          # ChromaDB client
│   │   └── workers/               # Background tasks
│   └── requirements.txt
├── frontend/                      # Streamlit UI
├── data/
│   ├── compliance_rules/          # Regulatory rules
│   ├── raw/                       # Uploaded documents
│   ├── processed/                 # Processed documents
│   ├── embeddings/                # Vector embeddings
│   └── compliance.db              # SQLite database
└── README.md
```

## 🛠️ Troubleshooting

### Tesseract OCR not found
- Ensure Tesseract is installed
- Set correct `TESSERACT_PATH` in `.env`
- Test: `tesseract --version`

### Database errors
- The SQLite database is created automatically
- Check that `data/` directory exists
- Database file: `data/compliance.db`

## 📝 Key Differences from Full Setup

This simplified version uses:
- **SQLite** instead of PostgreSQL (no database server needed)
- **Direct task execution** instead of Celery/Redis (no message queue needed)
- **Embedded processing** - all tasks run in the same process

Perfect for:
- Development and testing
- Single-user deployments
- Proof of concept
- Learning and experimentation

For production with multiple users, consider the full setup with PostgreSQL and Celery.

## ⚙️ Technology Stack

**Backend**: FastAPI, SQLAlchemy, Pydantic  
**AI/ML**: LangChain, OpenAI/Anthropic, Sentence Transformers  
**Document Processing**: Docling, PyMuPDF, Tesseract OCR, pdfplumber  
**Database**: SQLite (aiosqlite)  
**Vector Store**: ChromaDB  
**Frontend**: Streamlit  

---

**Built with**: FastAPI • LangChain • ChromaDB • SQLite • Streamlit • Tesseract OCR
