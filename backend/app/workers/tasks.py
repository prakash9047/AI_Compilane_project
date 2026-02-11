"""
Synchronous task processing (replaces Celery workers).
Tasks are executed directly without async queue.
"""
from loguru import logger
from app.db.database import AsyncSessionLocal
from app.db.models.document import Document, DocumentStatus
from app.db.models.validation import ValidationResult
from app.engines.extraction.extraction_engine import ExtractionEngine
from app.engines.segmentation.segmentation_engine import SegmentationEngine
from app.engines.rag.rag_pipeline import RAGPipeline
from app.engines.compliance.compliance_engine import ComplianceEngine
from sqlalchemy import select
from datetime import datetime
import uuid


async def process_document_task(document_id: int):
    """
    Process uploaded document: extract, segment, and index.
    
    Args:
        document_id: Document ID to process
    """
    logger.info(f"Processing document {document_id}")
    
    async with AsyncSessionLocal() as db:
        # Get document
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Update status
        document.status = DocumentStatus.PROCESSING
        document.processing_started_at = datetime.utcnow()
        await db.commit()
        
        try:
            # Extract content
            extraction_engine = ExtractionEngine()
            extracted = await extraction_engine.extract_document(document.file_path)
            
            document.extracted_text = extracted["text"]
            document.extracted_tables = extracted.get("tables", [])
            document.extracted_metadata = extracted.get("metadata", {})
            document.ocr_confidence = extracted.get("ocr_confidence")
            await db.commit()
            
            # Segment document
            segmentation_engine = SegmentationEngine()
            segments = await segmentation_engine.segment_document(
                extracted["text"],
                extracted.get("tables", [])
            )
            
            document.segments = segments
            document.segment_count = len(segments)
            document.status = DocumentStatus.SEGMENTED
            await db.commit()
            
            # Index in vector store
            rag_pipeline = RAGPipeline()
            await rag_pipeline.index_document(document_id, segments)
            
            # Mark as completed
            document.status = DocumentStatus.COMPLETED
            document.processing_completed_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Document {document_id} processed successfully")
            return {"status": "success", "document_id": document_id}
        
        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            await db.commit()
            logger.error(f"Document processing failed: {e}")
            raise


async def validate_document_task(document_id: int, framework: str):
    """
    Validate document against compliance rules.
    
    Args:
        document_id: Document ID
        framework: Regulatory framework
    """
    logger.info(f"Validating document {document_id} against {framework}")
    
    async with AsyncSessionLocal() as db:
        # Get document
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Run compliance validation
        compliance_engine = ComplianceEngine()
        validation_results = await compliance_engine.validate_document(
            segments=document.segments or [],
            framework=framework,
            document_text=document.extracted_text or ""
        )
        
        # Save results
        validation_run_id = str(uuid.uuid4())
        
        for result in validation_results:
            validation_record = ValidationResult(
                document_id=document_id,
                validation_run_id=validation_run_id,
                framework=framework,
                rule_id=result["rule_id"],
                rule_name=result["rule_name"],
                rule_description=result["rule_description"],
                status=result["status"],
                severity=result["severity"],
                confidence_score=result["confidence_score"],
                finding_summary=result["finding_summary"],
                finding_details=result.get("finding_details"),
                affected_sections=result.get("affected_sections"),
                evidence=result.get("evidence"),
                remediation_required=result.get("remediation_required", "no"),
                remediation_suggestions=result.get("remediation_suggestions"),
                ai_explanation=result.get("ai_explanation")
            )
            db.add(validation_record)
        
        document.status = "validated"
        await db.commit()
        
        logger.info(f"Validation complete for document {document_id}")
        return {"status": "success", "document_id": document_id, "framework": framework}
