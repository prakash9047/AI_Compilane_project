"""
Document model for storing document metadata and processing status.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum, JSON, Float
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class DocumentStatus(str, enum.Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    SEGMENTED = "segmented"
    VALIDATED = "validated"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    """Document type classification."""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    IMAGE = "image"
    XBRL = "xbrl"


class Document(Base):
    """Document metadata and processing information."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_type = Column(Enum(DocumentType), nullable=False)
    
    # Processing status
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Extracted content
    extracted_text = Column(Text, nullable=True)
    extracted_tables = Column(JSON, nullable=True)  # List of table data
    extracted_metadata = Column(JSON, nullable=True)  # Document metadata
    
    # Segmentation results
    segments = Column(JSON, nullable=True)  # List of document segments
    segment_count = Column(Integer, default=0)
    
    # Quality metrics
    ocr_confidence = Column(Float, nullable=True)
    extraction_quality_score = Column(Float, nullable=True)
    
    # User and timestamps
    uploaded_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"
