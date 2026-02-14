"""
Report generation API endpoints.
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models.document import Document
from app.db.models.validation import ComplianceReport
from loguru import logger

router = APIRouter()


@router.post("/{document_id}/generate")
async def generate_report(
    document_id: int,
    report_type: str = "full",
    db: AsyncSession = Depends(get_db)
):
    """
    Generate compliance report for a document.
    
    Args:
        document_id: Document ID
        report_type: Report type (full, summary, gap_analysis)
    """
    from sqlalchemy import select
    from app.workers.tasks import generate_report_task
    
    # Verify document exists
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Generate report directly (no Celery)
    try:
        result = await generate_report_task(document_id, report_type)
        logger.info(f"Report generated: {result}")
        
        return {
            "document_id": document_id,
            "report_type": report_type,
            "report_id": result.get("report_id"),
            "compliance_score": result.get("compliance_score"),
            "message": "Report generated successfully"
        }
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/reports")
async def list_reports(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List all reports for a document."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(ComplianceReport)
        .where(ComplianceReport.document_id == document_id)
        .order_by(ComplianceReport.generated_at.desc())
    )
    reports = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "report_type": r.report_type,
            "compliance_score": r.overall_compliance_score,
            "total_rules": r.total_rules_checked,
            "rules_passed": r.rules_passed,
            "rules_failed": r.rules_failed,
            "generated_at": r.generated_at,
            "pdf_available": r.pdf_path is not None,
            "excel_available": r.excel_path is not None
        }
        for r in reports
    ]


@router.get("/{report_id}/download/{format}")
async def download_report(
    report_id: int,
    format: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Download report in specified format.
    
    Args:
        report_id: Report ID
        format: Format (pdf, excel, json)
    """
    from sqlalchemy import select
    
    result = await db.execute(select(ComplianceReport).where(ComplianceReport.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Get file path based on format
    if format == "pdf":
        file_path = report.pdf_path
    elif format == "excel":
        file_path = report.excel_path
    elif format == "json":
        file_path = report.json_path
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use: pdf, excel, or json")
    
    if not file_path:
        raise HTTPException(status_code=404, detail=f"Report file not generated in {format} format")
    
    # Normalize path for cross-platform compatibility
    file_path = os.path.normpath(file_path)
    
    if not os.path.exists(file_path):
        logger.error(f"Report file not found at path: {file_path}")
        raise HTTPException(status_code=404, detail=f"Report file not found at: {file_path}")
    
    return FileResponse(
        path=file_path,
        filename=f"compliance_report_{report_id}.{format}",
        media_type="application/pdf" if format == "pdf" else "application/octet-stream"
    )

