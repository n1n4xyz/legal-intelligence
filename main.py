#!/usr/bin/env python3
"""
Legal Intelligence AI System - Main Application
===============================================
Welcome to LexiMind Solutions! You've been brought in as the Lead AI Architect
to fix our Legal Intelligence System. The infrastructure is built, but the AI
agents don't know how to think, analyze, or communicate.

Your mission: Make the agents intelligent by completing the TODOs.

Architecture:
- FastAPI server for API endpoints [WORKING]
- Multiple specialized agents [BROKEN - need personas]
- Chain-of-thought reasoning [BROKEN - not implemented]
- Quality validation [BROKEN - scoring algorithms missing]
- Context chaining between agents [BROKEN - no context passing]

Author: LexiMind Solutions Engineering Team
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add core modules to path
sys.path.append(str(Path(__file__).parent))

# Import core components
from src.core.agent_system import LegalIntelligenceAgent
from src.core.quality_validator import QualityValidator
from src.prompts.personas import LegalPersonas
from src.models.legal_models import (
    LegalScenario,
    AnalysisReport,
    AgentResponse,
    ValidationResult
)
from src.utils.logger import setup_logger

# Initialize logging
logger = setup_logger("legal-intelligence")

# Initialize FastAPI app
app = FastAPI(
    title="Legal Intelligence AI System",
    description="AI-powered legal analysis system with specialized agents",
    version="1.0.0"
)

# Global system state
system_state = {
    "initialized": False,
    "agent": None,
    "personas": None,
    "validator": None,
    "analysis_count": 0,
    "last_analysis": None
}

# Configuration
CONFIG = {
    "project_id": os.getenv("PROJECT_ID", ""),
    "location": os.getenv("LOCATION", "us-central1"),
    "model": os.getenv("MODEL", "gemini-2.0-flash"),
    "debug": os.getenv("DEBUG", "false").lower() == "true"
}


class SystemStatus(BaseModel):
    """System health and status response."""
    status: str
    initialized: bool
    configuration: Dict[str, Any]
    analysis_count: int
    last_analysis: Optional[str]
    available_agents: List[str]


class AnalysisRequest(BaseModel):
    """Request model for legal analysis."""
    case_name: str = Field(..., description="Name of the legal case")
    complaint_text: str = Field(..., description="Full text of the legal complaint")
    case_type: str = Field(..., description="Type of case (IP, Contract, Corporate, etc.)")
    urgency: str = Field(default="standard", description="Urgency level")
    additional_context: Optional[str] = Field(None, description="Additional context")


@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup."""
    try:
        logger.info("Starting Legal Intelligence AI System...")

        # Validate configuration
        if not CONFIG["project_id"]:
            logger.error("PROJECT_ID environment variable not set")
            raise ValueError("PROJECT_ID is required")

        # Initialize personas
        logger.info("Loading agent personas...")
        system_state["personas"] = LegalPersonas()

        # Initialize quality validator
        logger.info("Initializing quality validator...")
        system_state["validator"] = QualityValidator()

        # Initialize main agent system
        logger.info("Initializing Legal Intelligence Agent...")
        system_state["agent"] = LegalIntelligenceAgent(
            project_id=CONFIG["project_id"],
            location=CONFIG["location"],
            model_name=CONFIG["model"]
        )

        # Verify Vertex AI connection
        if system_state["agent"].initialize_vertex_ai():
            system_state["initialized"] = True
            logger.info("✅ System initialized successfully")
        else:
            logger.error("Failed to initialize Vertex AI")
            raise RuntimeError("Vertex AI initialization failed")

    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        system_state["initialized"] = False
        raise


@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "service": "Legal Intelligence AI System",
        "version": "1.0.0",
        "status": "operational" if system_state["initialized"] else "not_initialized",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if not system_state["initialized"]:
        raise HTTPException(status_code=503, detail="System not initialized")

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "vertex_ai": "connected",
            "personas": "loaded",
            "validator": "active"
        }
    }


@app.get("/status", response_model=SystemStatus)
async def get_status():
    """Get detailed system status."""
    return SystemStatus(
        status="operational" if system_state["initialized"] else "not_initialized",
        initialized=system_state["initialized"],
        configuration={
            "project_id": CONFIG["project_id"],
            "location": CONFIG["location"],
            "model": CONFIG["model"],
            "debug_mode": CONFIG["debug"]
        },
        analysis_count=system_state["analysis_count"],
        last_analysis=system_state["last_analysis"],
        available_agents=["business_analyst", "market_researcher", "strategic_consultant"]
    )


@app.post("/analyze")
async def analyze_case(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Main endpoint for legal case analysis.

    This endpoint:
    1. Receives a legal complaint
    2. Orchestrates multiple AI agents to analyze it
    3. Validates quality and retries if needed
    4. Returns a comprehensive strategic analysis
    """
    if not system_state["initialized"]:
        raise HTTPException(status_code=503, detail="System not initialized")

    try:
        logger.info(f"Starting analysis for case: {request.case_name}")
        start_time = time.time()

        # Create legal scenario from request
        scenario = LegalScenario(
            case_name=request.case_name,
            complaint_text=request.complaint_text,
            case_type=request.case_type,
            filing_date=datetime.now().isoformat(),
            parties_involved=_extract_parties(request.complaint_text),
            key_issues=_extract_key_issues(request.complaint_text, request.case_type),
            urgency_level=request.urgency,
            additional_context=request.additional_context
        )

        # Generate analysis report using the agent system
        report = await system_state["agent"].generate_complete_report(scenario)

        # Update system state
        system_state["analysis_count"] += 1
        system_state["last_analysis"] = datetime.now().isoformat()

        # Log success
        processing_time = time.time() - start_time
        logger.info(f"Analysis completed in {processing_time:.2f}s")

        # Schedule background quality check
        background_tasks.add_task(
            _background_quality_check,
            report,
            scenario
        )

        return JSONResponse(
            content=report.dict(),
            status_code=200
        )

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/validate")
async def validate_report(report: AnalysisReport):
    """
    Validate the quality of a generated report.

    Returns detailed validation results including:
    - Overall quality score
    - Section-specific scores
    - Improvement recommendations
    """
    if not system_state["initialized"]:
        raise HTTPException(status_code=503, detail="System not initialized")

    try:
        validation_result = system_state["validator"].validate_report(report)

        return {
            "overall_score": validation_result.overall_score,
            "passed": validation_result.passed,
            "section_scores": validation_result.section_scores,
            "issues": validation_result.issues,
            "recommendations": validation_result.recommendations
        }

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@app.get("/agents")
async def list_agents():
    """List available AI agents and their capabilities."""
    if not system_state["personas"]:
        raise HTTPException(status_code=503, detail="Personas not loaded")

    agents = []
    for agent_type in ["business_analyst", "market_researcher", "strategic_consultant"]:
        persona = system_state["personas"].get_persona(agent_type)
        agents.append({
            "type": agent_type,
            "name": agent_type.replace("_", " ").title(),
            "capabilities": _extract_capabilities(persona),
            "focus_areas": _extract_focus_areas(persona)
        })

    return {"agents": agents}


@app.get("/metrics")
async def get_metrics():
    """Get system performance metrics."""
    if not system_state["agent"]:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    return {
        "total_analyses": system_state["analysis_count"],
        "last_analysis": system_state["last_analysis"],
        "token_usage": system_state["agent"].get_token_usage_stats(),
        "quality_metrics": system_state["validator"].get_quality_metrics() if system_state["validator"] else None,
        "performance": {
            "average_processing_time": system_state["agent"].get_avg_processing_time(),
            "success_rate": system_state["agent"].get_success_rate()
        }
    }


@app.post("/reset")
async def reset_system():
    """Reset the system (admin endpoint)."""
    try:
        # Re-initialize components
        await startup_event()

        # Reset counters
        system_state["analysis_count"] = 0
        system_state["last_analysis"] = None

        return {"message": "System reset successfully"}

    except Exception as e:
        logger.error(f"Reset failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


# Helper functions

def _extract_parties(complaint_text: str) -> List[str]:
    """Extract party names from complaint text."""
    # Simplified extraction - in production would use NER
    parties = []

    # Look for common patterns
    lines = complaint_text.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        if 'plaintiff' in line.lower() or 'defendant' in line.lower():
            # Extract entity names (simplified)
            words = line.split()
            for i, word in enumerate(words):
                if word.lower() in ['plaintiff', 'defendant'] and i > 0:
                    parties.append(words[i-1])

    return parties if parties else ["Party A", "Party B"]


def _extract_key_issues(complaint_text: str, case_type: str) -> List[str]:
    """Extract key legal issues from complaint."""
    issues = []

    # Case type specific issues
    if "IP" in case_type or "intellectual" in case_type.lower():
        ip_terms = ["patent", "trademark", "copyright", "trade secret", "infringement"]
        for term in ip_terms:
            if term in complaint_text.lower():
                issues.append(f"{term.title()} dispute")

    elif "contract" in case_type.lower():
        contract_terms = ["breach", "performance", "termination", "damages"]
        for term in contract_terms:
            if term in complaint_text.lower():
                issues.append(f"Contract {term}")

    # Default issues if none found
    if not issues:
        issues = ["Primary legal dispute", "Damages assessment", "Remedy determination"]

    return issues


def _extract_capabilities(persona_text: str) -> List[str]:
    """Extract capabilities from persona description."""
    capabilities = []

    if "quantitative" in persona_text.lower():
        capabilities.append("Quantitative analysis")
    if "strategic" in persona_text.lower():
        capabilities.append("Strategic planning")
    if "competitive" in persona_text.lower():
        capabilities.append("Competitive intelligence")
    if "risk" in persona_text.lower():
        capabilities.append("Risk assessment")
    if "financial" in persona_text.lower():
        capabilities.append("Financial modeling")

    return capabilities if capabilities else ["Analysis", "Assessment", "Recommendations"]


def _extract_focus_areas(persona_text: str) -> List[str]:
    """Extract focus areas from persona description."""
    focus_areas = []

    # Look for specific frameworks mentioned
    if "TAM" in persona_text or "market size" in persona_text.lower():
        focus_areas.append("Market sizing")
    if "Porter" in persona_text:
        focus_areas.append("Industry analysis")
    if "SWOT" in persona_text:
        focus_areas.append("Strategic positioning")
    if "ROI" in persona_text or "NPV" in persona_text:
        focus_areas.append("Financial evaluation")

    return focus_areas if focus_areas else ["Business analysis", "Strategic insights"]


async def _background_quality_check(report: AnalysisReport, scenario: LegalScenario):
    """Run quality checks in the background."""
    try:
        logger.info(f"Running background quality check for {scenario.case_name}")

        validation_result = system_state["validator"].validate_report(report)

        if not validation_result.passed:
            logger.warning(f"Quality check failed for {scenario.case_name}: Score {validation_result.overall_score:.2f}")
            # In production, might trigger alerts or store for review
        else:
            logger.info(f"Quality check passed for {scenario.case_name}: Score {validation_result.overall_score:.2f}")

    except Exception as e:
        logger.error(f"Background quality check failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI application
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=CONFIG["debug"],
        log_level="info" if CONFIG["debug"] else "warning"
    )