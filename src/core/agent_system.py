"""
Legal Intelligence Agent System - Core Agent Implementation
===========================================================
CRITICAL: This module is BROKEN. The agents can't connect to Vertex AI,
generate content, or work together. You need to fix it!

The infrastructure is here, but the intelligence is missing.
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

# Google AI imports
from google import genai
from google.genai import types

# Internal imports
from ..models.legal_models import (
    LegalScenario,
    AnalysisReport,
    AgentResponse,
    ReportSection,
    TokenUsage
)
from ..prompts.personas import LegalPersonas
from .quality_validator import QualityValidator

logger = logging.getLogger(__name__)


class LegalIntelligenceAgent:
    """
    Main orchestrator for the Legal Intelligence AI System.

    CURRENT STATE: BROKEN
    - Can't connect to Vertex AI
    - Can't generate content
    - Can't chain context between agents

    YOUR MISSION: Fix the TODOs to make this system work!
    """

    def __init__(self, project_id: str, location: str = "us-central1", model_name: str = "gemini-2.0-flash"):
        """Initialize the Legal Intelligence Agent system."""
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.client = None
        self.initialized = False

        # Components
        self.personas = LegalPersonas()
        self.quality_validator = QualityValidator()

        # Performance tracking
        self.token_usage_history = []
        self.processing_times = []
        self.success_count = 0
        self.total_attempts = 0

        # Configuration
        self.generation_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=2048,
        )

        logger.info(f"LegalIntelligenceAgent initialized for project {project_id}")

    def initialize_vertex_ai(self) -> bool:
        """
        TODO 1: Initialize Vertex AI and create model instance.

        CURRENT STATE: Always returns False, can't connect to Vertex AI

        Requirements:
        1. Initialize Google Gen AI client with Vertex AI support
        2. Create a client instance configured for the project and location
        3. Test the connection with a simple prompt
        4. Handle errors gracefully and log them
        5. Set self.initialized = True if successful

        Hints:
        - Use genai.Client(vertexai=True, project=..., location=...)
        - Store the client in self.client
        - Test with client.models.generate_content()
        - Catch exceptions and log errors

        Expected imports are already included at the top of this file.
        """
        try:
            logger.info(f"Initializing Vertex AI for project: {self.project_id}")

            # TODO 1: Initialize Vertex AI
            # YOUR CODE HERE (approximately 10-15 lines)
            # Steps:
            # 1. Initialize vertexai with project and location
            # 2. Create the GenerativeModel instance
            # 3. Test with a simple prompt
            # 4. Check the response
            # 5. Set self.initialized = True if successful
            # 6. Return True for success, False for failure

            logger.error("TODO 1 not implemented: Vertex AI initialization failed")
            return False

        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {str(e)}")
            self.initialized = False
            return False

    def generate_section_content(
        self,
        persona: str,
        section_type: str,
        scenario: LegalScenario,
        previous_sections: List[ReportSection] = None
    ) -> Tuple[str, TokenUsage, float]:
        """
        TODO 2: Generate content for a specific report section.

        CURRENT STATE: Returns dummy content, no actual AI generation

        Requirements:
        1. Build a comprehensive prompt combining persona, scenario, and context
        2. Generate content using self.model with retry logic
        3. Track token usage from response.usage_metadata
        4. Calculate cost based on tokens
        5. Handle errors with exponential backoff

        Args:
            persona: The agent persona text (from personas.py)
            section_type: Type of section (e.g., "liability_assessment")
            scenario: The legal case to analyze
            previous_sections: Previous sections for context chaining

        Returns:
            Tuple of (content, token_usage, cost)

        Hints:
        - Use self._build_prompt() to create the prompt
        - Use self.model.generate_content() with self.generation_config
        - Implement retry with exponential backoff (2^attempt seconds)
        - Extract token counts from response.usage_metadata
        - Use self._calculate_cost() for cost calculation
        """
        if not self.initialized:
            raise RuntimeError("Agent system not initialized. Call initialize_vertex_ai() first.")

        start_time = time.time()
        previous_sections = previous_sections or []

        # Build the comprehensive prompt
        prompt = self._build_prompt(persona, section_type, scenario, previous_sections)

        # TODO 2: Implement content generation with retry logic
        # YOUR CODE HERE (approximately 25-35 lines)
        # Steps:
        # 1. Set max_retries = 3
        # 2. Loop for retry attempts
        # 3. Try to generate content using self.model.generate_content()
        # 4. Extract text from response
        # 5. Create TokenUsage from response.usage_metadata
        # 6. Calculate cost using self._calculate_cost()
        # 7. Handle exceptions with exponential backoff
        # 8. Return (content, token_usage, cost)

        # DUMMY IMPLEMENTATION - REPLACE THIS!
        logger.warning("TODO 2 not implemented: Using dummy content")
        dummy_content = f"[BROKEN] This is dummy content for {section_type}. The AI generation is not working."
        dummy_tokens = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
        dummy_cost = 0.01

        return dummy_content, dummy_tokens, dummy_cost

    async def generate_complete_report(self, scenario: LegalScenario) -> AnalysisReport:
        """
        TODO 3: Generate a complete analysis report.

        CURRENT STATE: Generates dummy report with no real analysis

        Requirements:
        1. Define section generation sequence with persona assignments
        2. Generate each section using generate_section_content()
        3. Pass previous sections for context chaining
        4. Validate quality and retry if below threshold
        5. Assemble final report with all sections

        The section sequence should be:
        - liability_assessment (business_analyst)
        - damage_calculation (business_analyst)
        - prior_art_analysis (market_researcher)
        - competitive_landscape (market_researcher)
        - risk_assessment (strategic_consultant)
        - strategic_recommendations (strategic_consultant)

        Hints:
        - Create section_config list with (section_type, persona) tuples
        - Use self.personas.get_persona() to get persona text
        - Pass sections list to generate_section_content for context
        - Use self.quality_validator.validate_section() to check quality
        - Retry with enhanced prompt if quality < 0.7
        """
        logger.info(f"Starting complete report generation for case: {scenario.case_name}")
        start_time = time.time()

        # TODO 3: Implement complete report generation
        # YOUR CODE HERE (approximately 40-60 lines)
        # Steps:
        # 1. Define section_config with (section_type, persona) pairs
        # 2. Initialize sections list and total_cost
        # 3. Loop through section_config
        # 4. Get persona using self.personas.get_persona()
        # 5. Generate content using: await asyncio.to_thread(self.generate_section_content, ...)
        #    IMPORTANT: Use asyncio.to_thread() to prevent blocking the event loop!
        # 6. Validate quality using self.quality_validator.validate_section()
        # 7. Retry if quality < 0.7 (also use asyncio.to_thread for retry)
        # 8. Create ReportSection objects
        # 9. Assemble final AnalysisReport

        # DUMMY IMPLEMENTATION - REPLACE THIS!
        logger.warning("TODO 3 not implemented: Generating dummy report")

        dummy_sections = [
            ReportSection(
                type="liability_assessment",
                title="Liability Assessment",
                content="[BROKEN] Dummy liability content",
                agent_type="business_analyst",
                quality_score=0.5,
                tokens_used=100,
                cost=0.01,
                timestamp=datetime.now().isoformat()
            )
        ]

        dummy_report = AnalysisReport(
            scenario=scenario,
            sections=dummy_sections,
            executive_summary="[BROKEN] System not working - TODOs not implemented",
            total_cost=0.01,
            total_tokens=100,
            processing_time=1.0,
            confidence_score=0.5,
            timestamp=datetime.now().isoformat(),
            metadata={"error": "TODOs not implemented"}
        )

        return dummy_report

    def _build_prompt(
        self,
        persona: str,
        section_type: str,
        scenario: LegalScenario,
        previous_sections: List[ReportSection]
    ) -> str:
        """Build a comprehensive prompt combining persona, context, and chain-of-thought instructions."""

        # Start with the persona
        prompt = persona + "\n\n"

        # Add chain-of-thought reasoning instructions
        prompt += """
REASONING INSTRUCTIONS:
You must use step-by-step reasoning to analyze this legal case. Structure your analysis as follows:
1. First, identify the key legal issues
2. Second, analyze the relevant facts
3. Third, apply legal principles
4. Finally, provide your conclusions

Think through each step carefully before moving to the next.
"""

        # Add context from previous sections if available
        if previous_sections:
            prompt += "\n\nPREVIOUS ANALYSIS:\n"
            for section in previous_sections[-2:]:  # Include last 2 sections for context
                prompt += f"\n{section.title}:\n"
                prompt += f"{section.content[:500]}...\n"  # Include summary

        # Add the specific task
        prompt += f"\n\nTASK: Provide a {section_type.replace('_', ' ')} for the following legal case:\n\n"

        # Add case details
        prompt += f"Case Name: {scenario.case_name}\n"
        prompt += f"Case Type: {scenario.case_type}\n"
        prompt += f"Key Issues: {', '.join(scenario.key_issues)}\n"
        prompt += f"Urgency: {scenario.urgency_level}\n\n"
        prompt += f"Complaint Summary:\n{scenario.complaint_text[:1500]}\n\n"

        # Add section-specific instructions
        prompt += self._get_section_instructions(section_type)

        return prompt

    def _get_section_instructions(self, section_type: str) -> str:
        """Get specific instructions for each section type."""
        instructions = {
            "liability_assessment": """
Analyze liability by:
- Identifying each potential claim
- Evaluating strength of evidence
- Assessing probability of success (use percentages)
- Citing relevant precedents or legal principles
""",
            "damage_calculation": """
Calculate potential damages by:
- Identifying categories of damages (actual, statutory, punitive)
- Providing specific dollar ranges
- Explaining calculation methodology
- Considering mitigation factors
""",
            "prior_art_analysis": """
Analyze prior art and precedents by:
- Identifying relevant existing patents/IP
- Assessing validity challenges
- Evaluating obviousness arguments
- Determining freedom to operate
""",
            "competitive_landscape": """
Analyze competitive implications by:
- Identifying key competitors affected
- Assessing market position changes
- Evaluating licensing opportunities
- Predicting competitor responses
""",
            "risk_assessment": """
Assess risks by:
- Identifying legal risks (probability and impact)
- Evaluating business risks
- Analyzing reputational risks
- Providing risk mitigation strategies
""",
            "strategic_recommendations": """
Provide strategic recommendations by:
- Outlining 3-5 specific action items
- Prioritizing by impact and urgency
- Estimating resource requirements
- Defining success metrics
"""
        }
        return instructions.get(section_type, "Provide comprehensive analysis for this section.")

    def _get_expected_elements(self, section_type: str) -> List[str]:
        """Get expected elements for quality validation."""
        elements_map = {
            "liability_assessment": ["claims", "evidence", "probability", "precedent"],
            "damage_calculation": ["damages", "calculation", "amount", "methodology"],
            "prior_art_analysis": ["patents", "prior art", "validity", "obviousness"],
            "competitive_landscape": ["competitors", "market", "position", "licensing"],
            "risk_assessment": ["risks", "probability", "impact", "mitigation"],
            "strategic_recommendations": ["recommendations", "action", "timeline", "resources"]
        }
        return elements_map.get(section_type, ["analysis", "assessment", "conclusion"])

    def _get_section_title(self, section_type: str) -> str:
        """Get formatted title for section."""
        titles = {
            "liability_assessment": "Liability Assessment",
            "damage_calculation": "Damage Calculation",
            "prior_art_analysis": "Prior Art Analysis",
            "competitive_landscape": "Competitive Landscape",
            "risk_assessment": "Risk Assessment",
            "strategic_recommendations": "Strategic Recommendations"
        }
        return titles.get(section_type, section_type.replace("_", " ").title())

    def _get_agent_type(self, persona: str) -> str:
        """Determine agent type from persona text."""
        if "Business Analyst" in persona:
            return "business_analyst"
        elif "Market Research" in persona:
            return "market_researcher"
        elif "Strategic" in persona:
            return "strategic_consultant"
        else:
            return "unknown"

    def _generate_executive_summary(self, sections: List[ReportSection], scenario: LegalScenario) -> str:
        """Generate executive summary from all sections."""
        summary = f"EXECUTIVE SUMMARY - {scenario.case_name}\n"
        summary += "=" * 50 + "\n\n"

        # Extract key points from each section
        for section in sections:
            # Get first substantive paragraph
            paragraphs = [p.strip() for p in section.content.split('\n\n') if len(p.strip()) > 50]
            if paragraphs:
                summary += f"{section.title}:\n"
                summary += f"{paragraphs[0][:200]}...\n\n"

        # Add overall assessment
        avg_quality = sum(s.quality_score for s in sections) / len(sections) if sections else 0
        summary += f"Overall Confidence: {avg_quality:.1%}\n"
        summary += f"Key Issues Identified: {len(scenario.key_issues)}\n"
        summary += f"Urgency Level: {scenario.urgency_level}\n"

        return summary

    def _calculate_cost(self, token_usage: TokenUsage) -> float:
        """Calculate cost based on token usage."""
        # Example pricing (adjust based on actual Vertex AI pricing)
        # Gemini pricing as of 2024: ~$0.00025 per 1K input tokens, ~$0.00125 per 1K output tokens
        input_cost = (token_usage.input_tokens / 1000) * 0.00025
        output_cost = (token_usage.output_tokens / 1000) * 0.00125
        return input_cost + output_cost

    # Metric tracking methods

    def get_token_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics."""
        if not self.token_usage_history:
            return {"error": "No usage data available"}

        total_input = sum(u.input_tokens for u in self.token_usage_history)
        total_output = sum(u.output_tokens for u in self.token_usage_history)
        total_tokens = sum(u.total_tokens for u in self.token_usage_history)

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_tokens,
            "average_per_request": total_tokens / len(self.token_usage_history) if self.token_usage_history else 0,
            "request_count": len(self.token_usage_history)
        }

    def get_avg_processing_time(self) -> float:
        """Get average processing time."""
        if not self.processing_times:
            return 0.0
        return sum(self.processing_times) / len(self.processing_times)

    def get_success_rate(self) -> float:
        """Get success rate of generations."""
        if self.total_attempts == 0:
            return 0.0
        return self.success_count / self.total_attempts