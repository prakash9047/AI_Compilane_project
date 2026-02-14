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


async def generate_report_task(document_id: int, report_type: str = "full"):
    """
    Generate compliance report for a document.
    
    Args:
        document_id: Document ID
        report_type: Type of report (full, summary, gap_analysis)
    """
    logger.info(f"Generating {report_type} report for document {document_id}")
    
    async with AsyncSessionLocal() as db:
        # Get document
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Get validation results
        from app.db.models.validation import ValidationResult, ComplianceReport
        result = await db.execute(
            select(ValidationResult).where(ValidationResult.document_id == document_id)
        )
        validation_results = result.scalars().all()
        
        if not validation_results:
            logger.warning(f"No validation results found for document {document_id}")
            return {"status": "error", "message": "No validation results available"}
        
        # Calculate summary statistics
        total_rules = len(validation_results)
        rules_passed = sum(1 for r in validation_results if r.status == "compliant")
        rules_failed = sum(1 for r in validation_results if r.status == "non_compliant")
        compliance_score = (rules_passed / total_rules * 100) if total_rules > 0 else 0
        
        # Get validation_run_id from first result (all results from same run have same ID)
        validation_run_id = validation_results[0].validation_run_id if validation_results else str(uuid.uuid4())
        
        # Generate PDF file
        import os
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.units import inch
        
        # Create reports directory if it doesn't exist
        reports_dir = "backend/reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate PDF filename
        pdf_filename = f"compliance_report_{document_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(reports_dir, pdf_filename)
        
        # Create PDF
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph("Compliance Validation Report", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Document Info
        info_data = [
            ["Document:", document.original_filename or document.filename],
            ["Report Type:", report_type.upper()],
            ["Generated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Framework:", validation_results[0].framework if validation_results else "N/A"]
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Summary Statistics
        story.append(Paragraph("Summary", styles['Heading2']))
        summary_data = [
            ["Metric", "Value"],
            ["Compliance Score", f"{compliance_score:.1f}%"],
            ["Total Rules Checked", str(total_rules)],
            ["Rules Passed", str(rules_passed)],
            ["Rules Failed", str(rules_failed)]
        ]
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Detailed Findings
        story.append(Paragraph("Detailed Findings", styles['Heading2']))
        story.append(Spacer(1, 0.2*inch))
        
        for idx, result in enumerate(validation_results[:20], 1):  # Limit to first 20 for PDF size
            # Rule header
            rule_title = f"{idx}. {result.rule_name}"
            story.append(Paragraph(rule_title, styles['Heading3']))
            
            # Status color
            status_color = colors.green if result.status == "compliant" else colors.red if result.status == "non_compliant" else colors.orange
            
            finding_data = [
                ["Status:", result.status.upper()],
                ["Severity:", result.severity],
                ["Confidence:", f"{result.confidence_score:.1%}"],
                ["Description:", result.rule_description or "N/A"]
            ]
            
            finding_table = Table(finding_data, colWidths=[1.5*inch, 4.5*inch])
            finding_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (1, 0), (1, 0), status_color),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(finding_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF generated at: {pdf_path}")
        
        # Create report record
        report = ComplianceReport(
            document_id=document_id,
            report_type=report_type,
            validation_run_id=validation_run_id,
            overall_compliance_score=compliance_score,
            total_rules_checked=total_rules,
            rules_passed=rules_passed,
            rules_failed=rules_failed,
            pdf_path=pdf_path,
            generated_at=datetime.utcnow()
        )
        
        db.add(report)
        await db.commit()
        await db.refresh(report)
        
        logger.info(f"Report {report.id} generated successfully for document {document_id}")
        return {
            "status": "success",
            "report_id": report.id,
            "document_id": document_id,
            "compliance_score": compliance_score,
            "pdf_path": pdf_path
        }

