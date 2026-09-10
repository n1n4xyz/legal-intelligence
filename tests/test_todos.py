#!/usr/bin/env python3
"""
Test Suite for Legal Intelligence AI System TODOs
=================================================
Run these tests to validate your TODO implementations.

Usage:
    python tests/test_todos.py

Each test corresponds to a specific TODO in the project.
"""

import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import modules to test
from src.core.agent_system import LegalIntelligenceAgent
from src.core.quality_validator import QualityValidator
from src.prompts.personas import LegalPersonas
from src.models.legal_models import LegalScenario, TokenUsage


class TestTODO1_VertexAIInitialization(unittest.TestCase):
    """Test TODO 1: Vertex AI Initialization"""

    def setUp(self):
        """Set up test environment."""
        self.project_id = os.getenv("PROJECT_ID", "test-project")
        self.agent = LegalIntelligenceAgent(self.project_id)

    @patch('src.core.agent_system.vertexai')
    @patch('src.core.agent_system.GenerativeModel')
    def test_vertex_ai_initialization(self, mock_model_class, mock_vertexai):
        """Test that Vertex AI is properly initialized."""
        # Mock the model instance
        mock_model = Mock()
        mock_model.generate_content.return_value = Mock(text="OK")
        mock_model_class.return_value = mock_model

        # Call initialize
        result = self.agent.initialize_vertex_ai()

        # Verify initialization was called
        mock_vertexai.init.assert_called_once_with(
            project=self.project_id,
            location=self.agent.location
        )

        # Verify model was created
        mock_model_class.assert_called_once_with(self.agent.model_name)

        # Verify test prompt was sent
        mock_model.generate_content.assert_called()

        # Verify success
        self.assertTrue(result, "Initialization should return True on success")
        self.assertTrue(self.agent.initialized, "Agent should be marked as initialized")

    def test_initialization_failure_handling(self):
        """Test that initialization handles failures gracefully."""
        # Without mocking, this should fail but not crash
        result = self.agent.initialize_vertex_ai()

        # Should return False on failure
        self.assertFalse(result, "Should return False when initialization fails")
        self.assertFalse(self.agent.initialized, "Agent should not be marked as initialized")


class TestTODO2_ContentGeneration(unittest.TestCase):
    """Test TODO 2: Section Content Generation"""

    def setUp(self):
        """Set up test environment."""
        self.project_id = os.getenv("PROJECT_ID", "test-project")
        self.agent = LegalIntelligenceAgent(self.project_id)
        self.agent.initialized = True  # Mark as initialized for testing

    @patch.object(LegalIntelligenceAgent, '_build_prompt')
    def test_content_generation_with_retry(self, mock_build_prompt):
        """Test content generation with retry logic."""
        mock_build_prompt.return_value = "Test prompt"

        # Mock the model
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Generated legal analysis content"
        mock_response.usage_metadata = Mock(
            prompt_token_count=100,
            candidates_token_count=50,
            total_token_count=150
        )

        # First call fails, second succeeds (testing retry)
        mock_model.generate_content.side_effect = [
            Exception("Network error"),
            mock_response
        ]
        self.agent.model = mock_model

        # Create test scenario
        scenario = LegalScenario(
            case_name="Test Case",
            complaint_text="Test complaint",
            case_type="IP",
            filing_date="2024-01-01",
            parties_involved=["Party A", "Party B"],
            key_issues=["Issue 1"],
            urgency_level="standard"
        )

        # Generate content
        with patch('time.sleep'):  # Skip actual sleep in tests
            content, tokens, cost = self.agent.generate_section_content(
                persona="Test persona",
                section_type="liability_assessment",
                scenario=scenario
            )

        # Verify retry happened
        self.assertEqual(mock_model.generate_content.call_count, 2,
                        "Should retry once after failure")

        # Verify return values
        self.assertIsInstance(content, str, "Should return content string")
        self.assertIsInstance(tokens, TokenUsage, "Should return TokenUsage object")
        self.assertIsInstance(cost, float, "Should return cost as float")

        # Check token tracking
        self.assertEqual(tokens.input_tokens, 100)
        self.assertEqual(tokens.output_tokens, 50)
        self.assertEqual(tokens.total_tokens, 150)

    def test_content_generation_without_initialization(self):
        """Test that content generation fails without initialization."""
        self.agent.initialized = False

        scenario = LegalScenario(
            case_name="Test Case",
            complaint_text="Test complaint",
            case_type="IP",
            filing_date="2024-01-01",
            parties_involved=[],
            key_issues=[],
            urgency_level="standard"
        )

        with self.assertRaises(RuntimeError) as context:
            self.agent.generate_section_content(
                persona="Test",
                section_type="test",
                scenario=scenario
            )

        self.assertIn("not initialized", str(context.exception).lower())


class TestTODO3_CompleteReport(unittest.TestCase):
    """Test TODO 3: Complete Report Generation"""

    def setUp(self):
        """Set up test environment."""
        self.project_id = os.getenv("PROJECT_ID", "test-project")
        self.agent = LegalIntelligenceAgent(self.project_id)
        self.agent.initialized = True

    @patch.object(LegalIntelligenceAgent, 'generate_section_content')
    @patch.object(QualityValidator, 'validate_section')
    async def test_complete_report_generation(self, mock_validate, mock_generate):
        """Test complete report generation with all sections."""
        # Mock content generation
        mock_generate.return_value = (
            "Test content",
            TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            0.01
        )

        # Mock validation
        mock_quality = Mock()
        mock_quality.overall_score = 0.8  # Good quality
        mock_validate.return_value = mock_quality

        # Create test scenario
        scenario = LegalScenario(
            case_name="Test Case",
            complaint_text="Test complaint",
            case_type="IP",
            filing_date="2024-01-01",
            parties_involved=["Party A", "Party B"],
            key_issues=["Issue 1"],
            urgency_level="high"
        )

        # Generate report
        report = await self.agent.generate_complete_report(scenario)

        # Verify all sections were generated
        expected_sections = [
            "liability_assessment",
            "damage_calculation",
            "prior_art_analysis",
            "competitive_landscape",
            "risk_assessment",
            "strategic_recommendations"
        ]

        self.assertEqual(len(report.sections), len(expected_sections),
                        f"Should generate {len(expected_sections)} sections")

        for section in report.sections:
            self.assertIn(section.type, expected_sections,
                         f"Section type {section.type} should be in expected sections")

        # Verify context chaining (previous sections passed)
        call_count = mock_generate.call_count
        self.assertEqual(call_count, 6, "Should generate 6 sections")

        # Verify report metadata
        self.assertIsNotNone(report.executive_summary)
        self.assertGreater(report.total_tokens, 0)
        self.assertGreater(report.total_cost, 0)
        self.assertGreater(report.confidence_score, 0)


class TestTODO4_CoherenceScoring(unittest.TestCase):
    """Test TODO 4: Coherence Scoring Algorithm"""

    def setUp(self):
        """Set up test environment."""
        self.validator = QualityValidator()

    def test_coherence_high_quality_content(self):
        """Test coherence scoring on high-quality content."""
        # Well-structured content
        content = """
        This comprehensive analysis reveals significant legal implications.

        First, the patent infringement claim shows strong merit based on the evidence presented.
        The defendant's product clearly practices all elements of claims 1-5. Furthermore, the
        willful infringement argument is supported by documented notice.

        Second, the damage calculation indicates substantial financial impact. Our analysis
        shows lost profits exceeding $10 million. Additionally, price erosion has affected
        market positioning. Therefore, the total damages could reach $15-20 million.

        Finally, the strategic implications require immediate attention. The preliminary
        injunction hearing presents both risks and opportunities. However, with proper
        preparation, a favorable outcome is achievable.

        In conclusion, this case presents strong prospects for success with appropriate strategy.
        """

        score = self.validator.calculate_coherence_score(content, "liability_assessment")

        # High-quality content should score well
        self.assertGreater(score, 0.7, "Well-structured content should score > 0.7")
        self.assertLessEqual(score, 1.0, "Score should not exceed 1.0")

    def test_coherence_low_quality_content(self):
        """Test coherence scoring on low-quality content."""
        # Poor structure, no transitions
        content = "Patent bad. Damages big. Must win case. Very important."

        score = self.validator.calculate_coherence_score(content, "liability_assessment")

        # Low-quality content should score poorly
        self.assertLess(score, 0.5, "Poorly structured content should score < 0.5")
        self.assertGreaterEqual(score, 0.0, "Score should not be negative")

    def test_coherence_scoring_components(self):
        """Test individual components of coherence scoring."""
        # Content with specific features
        content_with_paragraphs = "Para 1.\n\nPara 2.\n\nPara 3."
        content_with_connectors = "Therefore, however, furthermore, consequently, the analysis shows."
        content_with_structure = "First, we analyze. Second, we evaluate. Finally, we conclude."

        # Each component should contribute to score
        score_paragraphs = self.validator.calculate_coherence_score(
            content_with_paragraphs, "test"
        )
        score_connectors = self.validator.calculate_coherence_score(
            content_with_connectors, "test"
        )
        score_structure = self.validator.calculate_coherence_score(
            content_with_structure, "test"
        )

        # All should be > 0 if properly implemented
        self.assertGreater(score_paragraphs, 0, "Paragraphs should contribute to score")
        self.assertGreater(score_connectors, 0, "Connectors should contribute to score")
        self.assertGreater(score_structure, 0, "Structure words should contribute to score")


class TestTODO5_GroundednessScoring(unittest.TestCase):
    """Test TODO 5: Groundedness Scoring Algorithm"""

    def setUp(self):
        """Set up test environment."""
        self.validator = QualityValidator()

    def test_groundedness_liability_section(self):
        """Test groundedness scoring for liability assessment."""
        # Content with legal terminology
        content = """
        The liability assessment reveals clear breach of duty by the defendant.
        Negligence is established through the evidence of causation between the
        defendant's actions and the plaintiff's damages. The claim shows strong
        merit based on established precedent.
        """

        expected_elements = ["liability", "breach", "evidence"]
        score = self.validator.calculate_groundedness_score(
            content, "liability_assessment", expected_elements
        )

        # Should score well with relevant keywords
        self.assertGreater(score, 0.6, "Content with relevant terms should score > 0.6")

    def test_groundedness_damage_section(self):
        """Test groundedness scoring for damage calculation."""
        content = """
        The damage calculation includes both actual damages and punitive damages.
        Economic loss amounts to $5 million based on lost profits calculation.
        Additional compensation for price erosion brings the quantum to $8 million.
        """

        expected_elements = ["damages", "calculation", "compensation"]
        score = self.validator.calculate_groundedness_score(
            content, "damage_calculation", expected_elements
        )

        # Should score well with damage-related terms
        self.assertGreater(score, 0.6, "Damage content should score > 0.6")

    def test_groundedness_missing_elements(self):
        """Test groundedness with missing expected elements."""
        content = "This is generic text without any specific legal terminology."

        expected_elements = ["patent", "infringement", "claims", "validity"]
        score = self.validator.calculate_groundedness_score(
            content, "prior_art_analysis", expected_elements
        )

        # Should score poorly without expected elements
        self.assertLess(score, 0.4, "Content missing expected elements should score < 0.4")

    def test_groundedness_reasoning_indicators(self):
        """Test that reasoning indicators contribute to score."""
        content = """
        Based on the evidence, the conclusion is clear. Due to the strong precedent,
        the claim will succeed. Because of these factors, we recommend proceeding.
        As a result of our analysis, the damages are substantial.
        """

        score = self.validator.calculate_groundedness_score(
            content, "strategic_recommendations", ["recommendation"]
        )

        # Reasoning indicators should boost score
        self.assertGreater(score, 0.3, "Content with reasoning should score > 0.3")


class TestTODO6_BusinessAnalystPersona(unittest.TestCase):
    """Test TODO 6: Business Analyst Persona"""

    def setUp(self):
        """Set up test environment."""
        self.personas = LegalPersonas()

    def test_business_analyst_persona_exists(self):
        """Test that business analyst persona is defined."""
        persona = self.personas.get_persona("business_analyst")

        self.assertIsNotNone(persona, "Business analyst persona should exist")
        self.assertIsInstance(persona, str, "Persona should be a string")

    def test_business_analyst_persona_quality(self):
        """Test business analyst persona meets quality criteria."""
        persona = self.personas.get_persona("business_analyst")
        validation = self.personas.validate_persona(persona)

        # Check validation criteria
        self.assertTrue(validation["has_role_definition"],
                       "Should have role definition (You are...)")
        self.assertTrue(validation["has_expertise_areas"],
                       "Should have expertise areas")
        self.assertTrue(validation["has_communication_style"],
                       "Should have communication style")
        self.assertTrue(validation["has_frameworks"],
                       "Should have analytical frameworks")
        self.assertTrue(validation["sufficient_length"],
                       "Should be at least 150 words")

        # Overall score
        self.assertGreaterEqual(validation["score"], 0.8,
                              "Persona should score >= 0.8")

    def test_business_analyst_specific_content(self):
        """Test business analyst has specific required content."""
        persona = self.personas.get_persona("business_analyst")

        # Should mention quantitative analysis
        self.assertIn("quantitative", persona.lower(),
                     "Should mention quantitative analysis")

        # Should mention damage calculations
        self.assertTrue(
            "damage" in persona.lower() or "calculation" in persona.lower(),
            "Should mention damage calculations"
        )

        # Should mention specific frameworks
        self.assertTrue(
            any(framework in persona for framework in
                ["Georgia-Pacific", "Panduit", "TAM", "reasonable royalty"]),
            "Should mention specific legal/business frameworks"
        )


class TestTODO7_MarketResearcherPersona(unittest.TestCase):
    """Test TODO 7: Market Researcher Persona"""

    def setUp(self):
        """Set up test environment."""
        self.personas = LegalPersonas()

    def test_market_researcher_persona_exists(self):
        """Test that market researcher persona is defined."""
        persona = self.personas.get_persona("market_researcher")

        self.assertIsNotNone(persona, "Market researcher persona should exist")
        self.assertIsInstance(persona, str, "Persona should be a string")

    def test_market_researcher_persona_quality(self):
        """Test market researcher persona meets quality criteria."""
        persona = self.personas.get_persona("market_researcher")
        validation = self.personas.validate_persona(persona)

        # Check all validation criteria
        self.assertTrue(validation["has_role_definition"],
                       "Should have role definition")
        self.assertTrue(validation["has_expertise_areas"],
                       "Should have expertise areas")
        self.assertTrue(validation["has_communication_style"],
                       "Should have communication style")
        self.assertTrue(validation["has_frameworks"],
                       "Should have analytical frameworks")
        self.assertTrue(validation["sufficient_length"],
                       "Should be at least 150 words")

        # Overall score
        self.assertGreaterEqual(validation["score"], 0.8,
                              "Persona should score >= 0.8")

    def test_market_researcher_specific_content(self):
        """Test market researcher has specific required content."""
        persona = self.personas.get_persona("market_researcher")

        # Should mention competitive analysis
        self.assertTrue(
            "competitive" in persona.lower() or "competitor" in persona.lower(),
            "Should mention competitive analysis"
        )

        # Should mention patents or prior art
        self.assertTrue(
            "patent" in persona.lower() or "prior art" in persona.lower(),
            "Should mention patents or prior art"
        )

        # Should mention market/industry analysis
        self.assertTrue(
            "market" in persona.lower() or "industry" in persona.lower(),
            "Should mention market or industry analysis"
        )


class TestTODO8_StrategicConsultantPersona(unittest.TestCase):
    """Test TODO 8: Strategic Consultant Persona"""

    def setUp(self):
        """Set up test environment."""
        self.personas = LegalPersonas()

    def test_strategic_consultant_persona_exists(self):
        """Test that strategic consultant persona is defined."""
        persona = self.personas.get_persona("strategic_consultant")

        self.assertIsNotNone(persona, "Strategic consultant persona should exist")
        self.assertIsInstance(persona, str, "Persona should be a string")

    def test_strategic_consultant_persona_quality(self):
        """Test strategic consultant persona meets quality criteria."""
        persona = self.personas.get_persona("strategic_consultant")
        validation = self.personas.validate_persona(persona)

        # Check all validation criteria
        self.assertTrue(validation["has_role_definition"],
                       "Should have role definition")
        self.assertTrue(validation["has_expertise_areas"],
                       "Should have expertise areas")
        self.assertTrue(validation["has_communication_style"],
                       "Should have communication style")
        self.assertTrue(validation["has_frameworks"],
                       "Should have analytical frameworks")
        self.assertTrue(validation["sufficient_length"],
                       "Should be at least 150 words")

        # Overall score
        self.assertGreaterEqual(validation["score"], 0.8,
                              "Persona should score >= 0.8")

    def test_strategic_consultant_specific_content(self):
        """Test strategic consultant has specific required content."""
        persona = self.personas.get_persona("strategic_consultant")

        # Should mention strategy
        self.assertIn("strateg", persona.lower(),
                     "Should mention strategy")

        # Should mention risk
        self.assertIn("risk", persona.lower(),
                     "Should mention risk assessment")

        # Should mention recommendations or implementation
        self.assertTrue(
            "recommendation" in persona.lower() or "implementation" in persona.lower(),
            "Should mention recommendations or implementation"
        )

        # Should mention business outcomes or ROI
        self.assertTrue(
            "business" in persona.lower() or "roi" in persona.lower(),
            "Should focus on business outcomes"
        )


def run_tests():
    """Run all tests and report results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestTODO1_VertexAIInitialization,
        TestTODO2_ContentGeneration,
        TestTODO3_CompleteReport,
        TestTODO4_CoherenceScoring,
        TestTODO5_GroundednessScoring,
        TestTODO6_BusinessAnalystPersona,
        TestTODO7_MarketResearcherPersona,
        TestTODO8_StrategicConsultantPersona,
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED! Your implementation is correct!")
    else:
        print("\n❌ SOME TESTS FAILED. Review the errors above.")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)