"""
Validation model for storing compliance validation results.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class SeverityLevel(str, enum.Enum):
    """Compliance issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceStatus(str, enum.Enum):
    """Overall compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    PENDING = "pending"


class RegulatoryFramework(str, enum.Enum):
    """Supported regulatory frameworks."""
    IND_AS = "ind_as"
    SEBI = "sebi"
    RBI = "rbi"
    COMPANIES_ACT = "companies_act"


class ValidationResult(Base):
    """Compliance validation results for documents."""
    
    __tablename__ = "validation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Validation metadata
    validation_run_id = Column(String(100), nullable=False, index=True)
    framework = Column(Enum(RegulatoryFramework), nullable=False)
    rule_id = Column(String(100), nullable=False)
    rule_name = Column(String(255), nullable=False)
    rule_description = Column(Text, nullable=True)
    
    # Results
    status = Column(Enum(ComplianceStatus), nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Findings
    finding_summary = Column(Text, nullable=False)
    finding_details = Column(JSON, nullable=True)  # Detailed findings
    affected_sections = Column(JSON, nullable=True)  # List of document sections
    
    # Evidence
    evidence = Column(JSON, nullable=True)  # Supporting evidence
    citations = Column(JSON, nullable=True)  # Source citations
    
    # Remediation
    remediation_required = Column(String(10), default="no")  # yes/no
    remediation_suggestions = Column(Text, nullable=True)
    remediation_priority = Column(Integer, nullable=True)  # 1-5
    
    # AI explanation
    ai_explanation = Column(Text, nullable=True)  # Explainable AI output
    
    # Timestamps
    validated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ValidationResult(id={self.id}, document_id={self.document_id}, rule={self.rule_id}, status={self.status})>"


class ComplianceReport(Base):
    """Aggregated compliance reports."""
    
    __tablename__ = "compliance_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Report metadata
    report_type = Column(String(50), nullable=False)  # full, summary, gap_analysis
    validation_run_id = Column(String(100), nullable=False, index=True)
    
    # Overall scores
    overall_compliance_score = Column(Float, nullable=False)  # 0-100
    total_rules_checked = Column(Integer, nullable=False)
    rules_passed = Column(Integer, nullable=False)
    rules_failed = Column(Integer, nullable=False)
    
    # Severity breakdown
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    
    # Report data
    executive_summary = Column(Text, nullable=True)
    detailed_findings = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    
    # Export paths
    pdf_path = Column(String(512), nullable=True)
    excel_path = Column(String(512), nullable=True)
    json_path = Column(String(512), nullable=True)
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ComplianceReport(id={self.id}, document_id={self.document_id}, score={self.overall_compliance_score})>"
