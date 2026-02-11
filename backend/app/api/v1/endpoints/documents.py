"""
Document management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os
import shutil
from datetime import datetime

from app.db.database import get_db
from app.db.models.document import Document, DocumentStatus, DocumentType
from app.core.config import settings
from app.workers.tasks import process_document_task
from loguru import logger
import asyncio

router = APIRouter()

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document for processing.
    File will be saved and processing will start immediately.
    """
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Determine document type
    doc_type = DocumentType.PDF if file_ext == ".pdf" else \
               DocumentType.DOCX if file_ext == ".docx" else \
               DocumentType.XLSX if file_ext == ".xlsx" else \
               DocumentType.IMAGE
    
    # Create document record
    document = Document(
        filename=file.filename,
        original_filename=file.filename,
        file_path="",  # Will be set after saving
        file_size=file_size,
        file_type=doc_type,
        status=DocumentStatus.UPLOADED
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Save file
    file_path = os.path.join(settings.UPLOAD_DIR, f"{document.id}_{file.filename}")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update file path
    document.file_path = file_path
    await db.commit()
    
    # Start processing task in background
    asyncio.create_task(process_document_task(document.id))
    
    logger.info(f"Document uploaded: {document.id} - {file.filename}")
    
    return {
        "id": document.id,
        "filename": document.filename,
        "status": document.status,
        "message": "Document uploaded and processing started"
    }


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get document details by ID."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "filename": document.filename,
        "status": document.status,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "segment_count": document.segment_count,
        "created_at": document.created_at,
        "processing_started_at": document.processing_started_at,
        "processing_completed_at": document.processing_completed_at
    }


@router.get("/")
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all documents with pagination."""
    result = await db.execute(
        select(Document)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "created_at": doc.created_at
        }
        for doc in documents
    ]
