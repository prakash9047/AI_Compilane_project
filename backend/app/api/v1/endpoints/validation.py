"""
Compliance validation API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db
from app.db.models.document import Document
from app.db.models.validation import ValidationResult, RegulatoryFramework
from loguru import logger

router = APIRouter()


@router.post("/{document_id}/validate")
async def validate_document(
    document_id: int,
    framework: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger compliance validation for a document.
    
    Args:
        document_id: Document ID
        framework: Regulatory framework (ind_as, sebi, rbi, companies_act)
    """
    from sqlalchemy import select
    from app.workers.tasks import validate_document_task
    import asyncio
    
    # Verify document exists
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Validate framework
    valid_frameworks = [f.value for f in RegulatoryFramework]
    if framework not in valid_frameworks:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid framework. Valid options: {', '.join(valid_frameworks)}"
        )
    
    # Start validation task in background
    asyncio.create_task(validate_document_task(document_id, framework))
    
    logger.info(f"Validation task started for document {document_id}")
    
    return {
        "document_id": document_id,
        "framework": framework,
        "message": "Validation started"
    }


@router.get("/{document_id}/results")
async def get_validation_results(
    document_id: int,
    framework: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get validation results for a document."""
    from sqlalchemy import select
    
    query = select(ValidationResult).where(ValidationResult.document_id == document_id)
    
    if framework:
        query = query.where(ValidationResult.framework == framework)
    
    result = await db.execute(query.order_by(ValidationResult.validated_at.desc()))
    results = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "rule_id": r.rule_id,
            "rule_name": r.rule_name,
            "framework": r.framework,
            "status": r.status,
            "severity": r.severity,
            "confidence_score": r.confidence_score,
            "finding_summary": r.finding_summary,
            "remediation_required": r.remediation_required,
            "validated_at": r.validated_at
        }
        for r in results
    ]


@router.get("/{document_id}/summary")
async def get_validation_summary(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get validation summary with statistics."""
    from sqlalchemy import select, func
    
    # Get all results
    result = await db.execute(
        select(ValidationResult).where(ValidationResult.document_id == document_id)
    )
    results = result.scalars().all()
    
    if not results:
        return {
            "document_id": document_id,
            "total_rules": 0,
            "message": "No validation results found"
        }
    
    # Calculate statistics
    total = len(results)
    compliant = sum(1 for r in results if r.status == "compliant")
    non_compliant = sum(1 for r in results if r.status == "non_compliant")
    partial = sum(1 for r in results if r.status == "partial")
    
    # Severity breakdown
    critical = sum(1 for r in results if r.severity == "critical")
    high = sum(1 for r in results if r.severity == "high")
    medium = sum(1 for r in results if r.severity == "medium")
    low = sum(1 for r in results if r.severity == "low")
    
    compliance_score = (compliant / total * 100) if total > 0 else 0
    
    return {
        "document_id": document_id,
        "total_rules": total,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "partial": partial,
        "compliance_score": round(compliance_score, 2),
        "severity_breakdown": {
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low
        }
    }
