#!/usr/bin/env python3
"""
Quality Ranking Tests
=====================
Rubric check: the validator must rank high-quality analysis above medium and
low-quality analysis, for coherence, groundedness and the combined score.

Usage:
    python tests/test_quality_ranking.py
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.quality_validator import QualityValidator


HIGH_QUALITY = """## Liability Assessment

First, the complaint alleges that CloudSync Pro practices every element of claims 1-5 and 10-15 of the '456 Patent. Based on the claim chart described in the complaint, direct infringement under 35 U.S.C. 271(a) is plausible, although the defendant will contest claim construction.

Second, the willfulness claim is supported by evidence of notice. TechFlow sent a notice letter on January 10, 2024, and DataSync continued selling the product. Therefore, enhanced damages under Halo Electronics v. Pulse Electronics are a realistic exposure, because continued sales after notice indicate knowledge of the patent.

Third, causation between the infringement and TechFlow's losses needs support. Market share fell from 45% to 32% after the launch, which indicates harm. However, other competitors could explain part of the decline, so the claim requires an apportionment analysis.

Finally, we estimate a 60-70% probability of success on infringement and a 35-45% probability on willfulness. As a result, TechFlow holds strong leverage ahead of the April 20, 2024 injunction hearing.

In conclusion, liability exposure for DataSync is significant, and the evidence of notice is the strongest element of the plaintiff's case.
"""

MEDIUM_QUALITY = """The defendant probably infringes the patent. The product seems similar to the patented system and the plaintiff sent a letter.

There could be damages because the plaintiff lost market share. The case looks reasonably strong for the plaintiff overall.
"""

LOW_QUALITY = "Patent bad. They copied. Must win."

EXPECTED = ["claims", "evidence", "probability", "precedent"]


class TestQualityRanking(unittest.TestCase):
    """High > medium > low for every scoring component the rubric names."""

    def setUp(self):
        self.validator = QualityValidator()

    def _scores(self, method, *args):
        return [method(text, *args) for text in (HIGH_QUALITY, MEDIUM_QUALITY, LOW_QUALITY)]

    def test_coherence_ranking(self):
        high, medium, low = self._scores(self.validator.calculate_coherence_score, "liability_assessment")
        print(f"\nCoherence     high={high:.2f} medium={medium:.2f} low={low:.2f}")
        self.assertGreater(high, medium)
        self.assertGreater(medium, low)

    def test_groundedness_ranking(self):
        high, medium, low = self._scores(
            self.validator.calculate_groundedness_score, "liability_assessment", EXPECTED
        )
        print(f"\nGroundedness  high={high:.2f} medium={medium:.2f} low={low:.2f}")
        self.assertGreater(high, medium)
        self.assertGreater(medium, low)

    def test_overall_ranking_and_threshold(self):
        results = [
            self.validator.validate_section(text, "liability_assessment", EXPECTED)
            for text in (HIGH_QUALITY, MEDIUM_QUALITY, LOW_QUALITY)
        ]
        high, medium, low = (r.overall_score for r in results)
        print(f"\nOverall       high={high:.2f} medium={medium:.2f} low={low:.2f}")
        self.assertGreater(high, medium)
        self.assertGreater(medium, low)
        self.assertGreaterEqual(high, 0.7, "High-quality sample should pass the 0.7 threshold")
        self.assertLess(low, 0.7, "Low-quality sample should fail the 0.7 threshold")
        self.assertTrue(results[2].feedback, "Low-quality sample should produce improvement feedback")

    def test_scores_stay_in_range(self):
        for text in (HIGH_QUALITY, MEDIUM_QUALITY, LOW_QUALITY, ""):
            c = self.validator.calculate_coherence_score(text, "risk_assessment")
            g = self.validator.calculate_groundedness_score(text, "risk_assessment", ["risk"])
            self.assertTrue(0.0 <= c <= 1.0)
            self.assertTrue(0.0 <= g <= 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)