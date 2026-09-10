"""
Data Models for Legal Intelligence AI System
============================================
Pydantic models for request/response validation and data structures.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class UrgencyLevel(str, Enum):
    """Urgency levels for legal cases."""
    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"
    CRITICAL = "critical"


class CaseType(str, Enum):
    """Types of legal cases."""
    INTELLECTUAL_PROPERTY = "IP"
    CONTRACT = "Contract"
    CORPORATE = "Corporate"
    ANTITRUST = "Antitrust"
    EMPLOYMENT = "Employment"
    REGULATORY = "Regulatory"
    OTHER = "Other"


class LegalScenario(BaseModel):
    """Represents a legal case scenario for analysis."""
    case_name: str = Field(..., description="Name/identifier of the case")
    complaint_text: str = Field(..., description="Full text of the legal complaint")
    case_type: str = Field(..., description="Type of legal case")
    filing_date: str = Field(..., description="Date of filing")
    parties_involved: List[str] = Field(default_factory=list, description="Parties in the case")
    key_issues: List[str] = Field(default_factory=list, description="Key legal issues identified")
    urgency_level: str = Field(default="standard", description="Urgency of the case")
    additional_context: Optional[str] = Field(None, description="Additional context or notes")

    class Config:
        json_schema_extra = {
            "example": {
                "case_name": "TechFlow Innovations v. DataSync Corp",
                "complaint_text": "Plaintiff TechFlow alleges patent infringement...",
                "case_type": "IP",
                "filing_date": "2024-01-15",
                "parties_involved": ["TechFlow Innovations", "DataSync Corp"],
                "key_issues": ["Patent infringement", "Damages calculation", "Injunctive relief"],
                "urgency_level": "high",
                "additional_context": "Preliminary injunction hearing scheduled"
            }
        }


class TokenUsage(BaseModel):
    """Token usage tracking for cost calculation."""
    input_tokens: int = Field(..., description="Number of input tokens used")
    output_tokens: int = Field(..., description="Number of output tokens generated")
    total_tokens: int = Field(..., description="Total tokens used")


class ReportSection(BaseModel):
    """A single section of the analysis report."""
    type: str = Field(..., description="Section type identifier")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    agent_type: str = Field(..., description="Agent that generated this section")
    quality_score: float = Field(..., description="Quality score for this section")
    tokens_used: int = Field(..., description="Tokens used for this section")
    cost: float = Field(..., description="Cost for generating this section")
    timestamp: str = Field(..., description="When this section was generated")


class AnalysisReport(BaseModel):
    """Complete analysis report for a legal case."""
    scenario: LegalScenario = Field(..., description="The analyzed scenario")
    sections: List[ReportSection] = Field(..., description="Report sections")
    executive_summary: str = Field(..., description="Executive summary")
    total_cost: float = Field(..., description="Total generation cost")
    total_tokens: int = Field(..., description="Total tokens used")
    processing_time: float = Field(..., description="Processing time in seconds")
    confidence_score: float = Field(..., description="Overall confidence score")
    timestamp: str = Field(..., description="Report generation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def dict(self, **kwargs):
        """Override dict to ensure proper serialization."""
        data = super().dict(**kwargs)
        # Ensure scenario is properly serialized
        if isinstance(data.get('scenario'), LegalScenario):
            data['scenario'] = data['scenario'].dict()
        return data


class AgentResponse(BaseModel):
    """Response from an individual agent."""
    agent_type: str = Field(..., description="Type of agent")
    content: str = Field(..., description="Generated content")
    reasoning: Optional[str] = Field(None, description="Chain-of-thought reasoning")
    confidence: float = Field(..., description="Confidence score")
    tokens_used: TokenUsage = Field(..., description="Token usage details")
    processing_time: float = Field(..., description="Processing time")


class ValidationResult(BaseModel):
    """Result from quality validation."""
    overall_score: float = Field(..., description="Overall quality score")
    passed: bool = Field(..., description="Whether validation passed")
    section_scores: Dict[str, float] = Field(..., description="Scores by section")
    issues: List[str] = Field(default_factory=list, description="Identified issues")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")


class SystemMetrics(BaseModel):
    """System performance metrics."""
    total_analyses: int = Field(..., description="Total analyses performed")
    average_processing_time: float = Field(..., description="Average processing time")
    success_rate: float = Field(..., description="Success rate")
    total_tokens_used: int = Field(..., description="Total tokens consumed")
    total_cost: float = Field(..., description="Total cost incurred")
    quality_metrics: Dict[str, float] = Field(default_factory=dict, description="Quality metrics")