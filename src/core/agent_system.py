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
from google.genai import errors as genai_errors

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


# ---------------------------------------------------------------------------
# Compatibility layer
# ---------------------------------------------------------------------------
# The project runs on the google-genai SDK (see requirements.txt). The provided
# tests in tests/test_todos.py were written against the retired
# vertexai.generative_models SDK and patch `vertexai` and `GenerativeModel` in
# this module. These two thin wrappers expose that older interface on top of
# genai.Client, so the tests and the real runtime go through one code path.
# ---------------------------------------------------------------------------

class _VertexAIClientFactory:
    """Mirrors vertexai.init() and holds a genai.Client configured for Vertex AI."""

    def __init__(self):
        self.client: Optional[genai.Client] = None

    def init(self, project: str, location: str) -> None:
        self.client = genai.Client(vertexai=True, project=project, location=location)


vertexai = _VertexAIClientFactory()


class GenerativeModel:
    """Mirrors GenerativeModel.generate_content() on top of genai.Client."""

    def __init__(self, model_name: str):
        if vertexai.client is None:
            raise RuntimeError("Call vertexai.init() before creating a GenerativeModel")
        self.model_name = model_name
        self._client = vertexai.client

    def generate_content(
        self,
        contents: Any,
        generation_config: Optional[types.GenerateContentConfig] = None
    ):
        return self._client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=generation_config
        )


class LegalIntelligenceAgent:
    """
    Main orchestrator for the Legal Intelligence AI System.

    CURRENT STATE: BROKEN
    - Can't connect to Vertex AI
    - Can't generate content
    - Can't chain context between agents

    YOUR MISSION: Fix the TODOs to make this system work!
    """

    def __init__(self, project_id: str, location: str = "us-central1", model_name: str = "gemini-2.5-flash"):
        """Initialize the Legal Intelligence Agent system."""
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.client = None
        self.model = None
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
            # Gemini 2.5 and newer count thinking tokens against this limit.
            # 2048 truncates sections or returns empty text, so allow more room.
            max_output_tokens=8192,
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
            # 1. Create the Vertex AI client for project and location
            vertexai.init(project=self.project_id, location=self.location)
            self.client = getattr(vertexai, "client", None)

            # 2. Create the model wrapper used by all agents
            self.model = GenerativeModel(self.model_name)

            # 3. Smoke test with a tiny prompt (a fraction of a cent)
            test_config = types.GenerateContentConfig(temperature=0.0, max_output_tokens=256)
            response = self.model.generate_content(
                "Reply with the single word OK.",
                generation_config=test_config
            )

            # 4. Any response without an exception proves auth, API and model ID work
            if response is None:
                raise RuntimeError("Vertex AI returned no response to the test prompt")
            logger.info(f"Vertex AI test response: {str(getattr(response, 'text', ''))[:50]!r}")

            # 5. Mark as ready
            self.initialized = True
            logger.info(f"Vertex AI ready: model={self.model_name}, location={self.location}")
            return True

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

        # TODO 2: Content generation with retry logic
        max_retries = 3
        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            self.total_attempts += 1
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=self.generation_config
                )

                content = (getattr(response, "text", None) or "").strip()
                if not content:
                    raise ValueError("Model returned empty content")

                # Token tracking. Thinking tokens are billed as output tokens.
                usage = getattr(response, "usage_metadata", None)
                input_tokens = self._as_int(getattr(usage, "prompt_token_count", 0))
                output_tokens = (
                    self._as_int(getattr(usage, "candidates_token_count", 0))
                    + self._as_int(getattr(usage, "thoughts_token_count", 0))
                )
                total_tokens = (
                    self._as_int(getattr(usage, "total_token_count", 0))
                    or input_tokens + output_tokens
                )
                token_usage = TokenUsage(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens
                )
                cost = float(self._calculate_cost(token_usage))

                # Performance tracking
                self.token_usage_history.append(token_usage)
                self.processing_times.append(time.time() - start_time)
                self.success_count += 1

                logger.info(
                    f"Generated {section_type} on attempt {attempt + 1}: "
                    f"{total_tokens} tokens, ${cost:.5f}"
                )
                return content, token_usage, cost

            except Exception as e:
                last_error = e

                # 400/403/404 will fail the same way again, so stop immediately
                if isinstance(e, genai_errors.ClientError) and getattr(e, "code", None) in (400, 401, 403, 404):
                    logger.error(f"Non-retryable error for {section_type}: {e}")
                    break

                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed for {section_type}: {e}"
                )
                if attempt < max_retries - 1:
                    wait_seconds = 2 ** attempt  # 1s, 2s
                    time.sleep(wait_seconds)

        raise RuntimeError(
            f"Content generation failed for {section_type} after retries: {last_error}"
        ) from last_error

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

        # TODO 3: Complete report generation
        # 1. Section sequence with persona assignments. Order matters: each
        #    specialist builds on the analysis of the ones before.
        section_config = [
            ("liability_assessment", "business_analyst"),
            ("damage_calculation", "business_analyst"),
            ("prior_art_analysis", "market_researcher"),
            ("competitive_landscape", "market_researcher"),
            ("risk_assessment", "strategic_consultant"),
            ("strategic_recommendations", "strategic_consultant"),
        ]

        quality_threshold = self.quality_validator.min_quality_threshold  # 0.7
        max_quality_retries = 2  # hard cap so a weak section can't loop forever

        # 2. Report state
        sections: List[ReportSection] = []          # everything that goes into the report
        context_sections: List[ReportSection] = []  # only successful sections feed the chain
        total_cost = 0.0
        total_tokens = 0
        quality_retries_used = 0
        below_threshold: List[str] = []
        failed_sections: List[Dict[str, str]] = []
        quality_audit: List[Dict[str, Any]] = []

        # 3. Generate each section in sequence
        for section_type, agent_type in section_config:
            persona = self.personas.get_persona(agent_type)
            expected_elements = self._get_expected_elements(section_type)
            attempt_scores: List[float] = []

            # 4. First attempt. Context chain: all previous sections are passed on.
            #    asyncio.to_thread keeps the FastAPI event loop responsive.
            try:
                content, usage, cost = await asyncio.to_thread(
                    self.generate_section_content,
                    persona,
                    section_type,
                    scenario,
                    list(context_sections)
                )
            except Exception as e:
                # Auth, permission or model-ID errors hit every section the same way: fail fast
                cause = e.__cause__ or e
                if isinstance(cause, genai_errors.ClientError) and getattr(cause, "code", None) in (400, 401, 403, 404):
                    raise

                # Transient failure: degrade gracefully, mark the gap and keep going
                logger.error(f"{section_type} failed after retries, continuing without it: {e}")
                failed_sections.append({"section": section_type, "error": str(e)[:200]})
                sections.append(ReportSection(
                    type=section_type,
                    title=self._get_section_title(section_type),
                    content=(
                        f"This section could not be generated ({type(cause).__name__}). "
                        f"Re-run the analysis before relying on this report."
                    ),
                    agent_type=agent_type,
                    quality_score=0.0,
                    tokens_used=0,
                    cost=0.0,
                    timestamp=datetime.now().isoformat()
                ))
                continue

            section_tokens = usage.total_tokens
            section_cost = cost
            quality = self.quality_validator.validate_section(content, section_type, expected_elements)
            attempt_scores.append(round(float(quality.overall_score), 3))

            best_content, best_quality = content, quality

            # 5. Quality validation loop: retry with the validator's feedback
            attempt = 0
            while best_quality.overall_score < quality_threshold and attempt < max_quality_retries:
                attempt += 1
                quality_retries_used += 1
                logger.info(
                    f"{section_type} scored {best_quality.overall_score:.2f} "
                    f"(< {quality_threshold}), retry {attempt}/{max_quality_retries}"
                )
                enhanced_persona = persona + self._build_quality_feedback(
                    best_quality, expected_elements, attempt
                )
                try:
                    content, usage, cost = await asyncio.to_thread(
                        self.generate_section_content,
                        enhanced_persona,
                        section_type,
                        scenario,
                        list(context_sections)
                    )
                except Exception as e:
                    logger.warning(f"Quality retry for {section_type} failed, keeping best version: {e}")
                    break

                section_tokens += usage.total_tokens
                section_cost += cost
                quality = self.quality_validator.validate_section(content, section_type, expected_elements)
                attempt_scores.append(round(float(quality.overall_score), 3))

                # Keep whichever version scores higher
                if quality.overall_score > best_quality.overall_score:
                    best_content, best_quality = content, quality

            if best_quality.overall_score < quality_threshold:
                below_threshold.append(section_type)
                logger.warning(
                    f"{section_type} stayed below threshold after retries: "
                    f"{best_quality.overall_score:.2f}"
                )

            # Audit trail: every attempt and the version that was kept
            quality_audit.append({
                "section": section_type,
                "agent": agent_type,
                "attempt_scores": attempt_scores,
                "selected_score": round(float(best_quality.overall_score), 3),
                "tokens": section_tokens,
                "cost_usd": round(section_cost, 6),
            })

            # 6. Store the section so the next specialist receives it as context
            section = ReportSection(
                type=section_type,
                title=self._get_section_title(section_type),
                content=best_content,
                agent_type=agent_type,
                quality_score=round(float(best_quality.overall_score), 3),
                tokens_used=section_tokens,
                cost=section_cost,
                timestamp=datetime.now().isoformat()
            )
            sections.append(section)
            context_sections.append(section)
            total_tokens += section_tokens
            total_cost += section_cost

        if not context_sections:
            raise RuntimeError(f"All report sections failed for {scenario.case_name}: {failed_sections}")

        # 7. Assemble the final report
        processing_time = time.time() - start_time
        confidence_score = sum(s.quality_score for s in sections) / len(sections)

        report = AnalysisReport(
            scenario=scenario,
            sections=sections,
            executive_summary=self._generate_executive_summary(sections, scenario),
            total_cost=round(total_cost, 6),
            total_tokens=total_tokens,
            processing_time=round(processing_time, 2),
            confidence_score=round(confidence_score, 3),
            timestamp=datetime.now().isoformat(),
            metadata={
                "model": self.model_name,
                "section_sequence": [s for s, _ in section_config],
                "context_chaining": "each section receives all previously completed sections",
                "quality_threshold": quality_threshold,
                "quality_retries_used": quality_retries_used,
                "sections_below_threshold": below_threshold,
                "failed_sections": failed_sections,
                "quality_audit": quality_audit,
                "success_rate": round(self.get_success_rate(), 3),
            }
        )

        logger.info(
            f"Report complete for {scenario.case_name}: {len(sections)} sections, "
            f"confidence {confidence_score:.2f}, {total_tokens} tokens, "
            f"${total_cost:.4f}, {processing_time:.1f}s"
        )
        return report

    def _build_quality_feedback(self, quality: Any, expected_elements: List[str], attempt: int) -> str:
        """Turn validator feedback into instructions appended to the persona for a retry."""
        feedback_items = getattr(quality, "feedback", None)
        feedback_items = feedback_items if isinstance(feedback_items, list) else []
        feedback_text = "\n".join(f"- {item}" for item in feedback_items) or "- Add depth and specific evidence"

        return (
            f"\n\nQUALITY REVIEW (retry {attempt}):\n"
            f"Your previous draft scored {quality.overall_score:.2f}, below the required 0.70.\n"
            f"Fix these issues:\n{feedback_text}\n"
            f"- Explicitly cover: {', '.join(expected_elements)}\n"
            f"- Write at least 4 paragraphs separated by blank lines\n"
            f"- Use First, Second, Finally to structure the reasoning\n"
            f"- Tie every conclusion to a fact or figure from the complaint\n"
            f"- End with a short conclusion paragraph\n"
        )

    @staticmethod
    def _as_int(value: Any) -> int:
        """Return value if it is a real int (SDK fields can be None), else 0."""
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

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
            prompt += "\n\nPREVIOUS ANALYSIS FROM OTHER SPECIALISTS (build on this, don't repeat it):\n"
            # All earlier sections, so the strategist also sees liability and damages.
            # The two most recent get more room because they're the closest context.
            for i, section in enumerate(previous_sections):
                limit = 1200 if i >= len(previous_sections) - 2 else 600
                prompt += f"\n{section.title} ({section.agent_type}):\n"
                prompt += f"{section.content[:limit]}...\n"

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

    # USD per 1M tokens, Vertex AI standard tier (checked September 2026).
    # Thinking tokens are billed at the output rate. Add a row when you switch models.
    MODEL_PRICING_PER_1M = {
        "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
        "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
    }

    def _calculate_cost(self, token_usage: TokenUsage) -> float:
        """Estimate cost from token usage using the pricing table for the active model."""
        pricing = self.MODEL_PRICING_PER_1M.get(self.model_name)
        if pricing is None:
            if not getattr(self, "_pricing_warned", False):
                logger.warning(
                    f"No pricing entry for {self.model_name}, estimating with gemini-2.5-flash rates"
                )
                self._pricing_warned = True
            pricing = self.MODEL_PRICING_PER_1M["gemini-2.5-flash"]
        input_cost = (token_usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (token_usage.output_tokens / 1_000_000) * pricing["output"]
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