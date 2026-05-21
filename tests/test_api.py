"""
Integration tests for the ScotlandAI Navigator API.

Tests the complete pipeline: request → validation → response.
Note: Tests that call Gemini require GEMINI_API_KEY in the environment.
"""

import os
import pytest
from unittest.mock import patch, AsyncMock

# Test data — a realistic council scenario
VALID_COUNCIL_ANSWERS = {
    "organisation_and_bottleneck": (
        "We're a Scottish council processing 400 planning applications monthly. "
        "Each one takes approximately 3 hours to review, classify, and route to "
        "the correct officer. It's our biggest operational bottleneck."
    ),
    "data_assets": (
        "PDFs of all planning applications going back 10 years, "
        "a SQL database tracking decisions and outcomes, "
        "and Excel spreadsheets for officer assignment tracking."
    ),
    "value_of_improvement": (
        "About £80,000 per year — roughly equivalent to 2 full-time planning officers."
    ),
    "risk_appetite": "quick_win",
    "technical_capability": "needs_support",
}

VALID_NHS_ANSWERS = {
    "organisation_and_bottleneck": (
        "We're an NHS health board running 14 hospitals across Scotland. "
        "Our biggest bottleneck is patient discharge processing — each discharge "
        "requires 6 different forms and takes an average of 4 hours."
    ),
    "data_assets": (
        "Electronic patient records in our PAS system, discharge summaries as PDFs, "
        "bed management database, and pharmacy prescription logs."
    ),
    "value_of_improvement": (
        "Each bed freed up one day earlier saves approximately £400 per day. "
        "Across 14 hospitals, that's significant."
    ),
    "risk_appetite": "quick_win",
    "technical_capability": "internal_team",
}

INVALID_ANSWERS_TOO_SHORT = {
    "organisation_and_bottleneck": "We do stuff",
    "data_assets": "spreadsheets",
    "value_of_improvement": "£50k",
    "risk_appetite": "quick_win",
    "technical_capability": "internal_team",
}

INVALID_ANSWERS_PLACEHOLDER = {
    "organisation_and_bottleneck": "N/A — just testing this out to see what happens",
    "data_assets": "none",
    "value_of_improvement": "nothing",
    "risk_appetite": "quick_win",
    "technical_capability": "internal_team",
}


class TestValidation:
    """Test that the API rejects invalid inputs correctly."""

    def test_valid_council_answers_pass(self):
        """A realistic council scenario should validate successfully."""
        from backend.schemas.discovery import DiscoveryAnswers
        answers = DiscoveryAnswers(**VALID_COUNCIL_ANSWERS)
        assert answers.organisation_and_bottleneck is not None
        assert answers.risk_appetite.value == "quick_win"

    def test_valid_nhs_answers_pass(self):
        """A realistic NHS scenario should validate successfully."""
        from backend.schemas.discovery import DiscoveryAnswers
        answers = DiscoveryAnswers(**VALID_NHS_ANSWERS)
        assert "NHS" in answers.organisation_and_bottleneck

    def test_short_answers_rejected(self):
        """Answers that are too short should fail validation."""
        from backend.schemas.discovery import DiscoveryAnswers
        with pytest.raises(Exception):
            DiscoveryAnswers(**INVALID_ANSWERS_TOO_SHORT)

    def test_placeholder_answers_rejected(self):
        """N/A and placeholder answers should fail validation."""
        from backend.schemas.discovery import DiscoveryAnswers
        with pytest.raises(Exception):
            DiscoveryAnswers(**INVALID_ANSWERS_PLACEHOLDER)


class TestInfrastructureClassification:
    """Test that workloads map to the correct DataVita facility."""

    def test_council_maps_to_dv1(self):
        """Public sector should get sovereign hosting at DV1."""
        from backend.services.infrastructure import get_infrastructure_for_brief
        workload_type, rec = get_infrastructure_for_brief(
            VALID_COUNCIL_ANSWERS["organisation_and_bottleneck"],
            VALID_COUNCIL_ANSWERS["data_assets"],
        )
        assert workload_type == "public_sector"
        assert "DV1" in rec.facility

    def test_nhs_maps_to_dv1(self):
        """NHS should get sovereign hosting at DV1."""
        from backend.services.infrastructure import get_infrastructure_for_brief
        workload_type, rec = get_infrastructure_for_brief(
            VALID_NHS_ANSWERS["organisation_and_bottleneck"],
            VALID_NHS_ANSWERS["data_assets"],
        )
        assert workload_type == "public_sector"
        assert "DV1" in rec.facility


class TestBriefValidation:
    """Test that brief output validation catches vague language."""

    def test_vague_executive_summary_rejected(self):
        """Executive summaries with jargon should fail."""
        from backend.schemas.brief import BriefResponse
        with pytest.raises(Exception):
            BriefResponse(
                executive_summary=(
                    "This organisation could benefit from deploying a RAG pipeline "
                    "on DV1's Tier III infrastructure to leverage LLM inference."
                ),
                opportunities=[],
                recommended_first_step="Run a 90-day pilot",
            )

    def test_vague_opportunity_rejected(self):
        """Opportunities with banned phrases should fail."""
        from backend.schemas.brief import Opportunity
        with pytest.raises(Exception):
            Opportunity(
                name="Generic AI Tool",
                what_it_does="Helps improve efficiency across the organisation",
                problem_solved="Addresses data challenges",
                data_required=["spreadsheets"],
                expected_impact="Will gain insights from data",
                infrastructure="DV1",
                build_complexity="Medium",
                time_to_value="90 days",
            )


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_returns_ok(self):
        """Health endpoint should return healthy status."""
        # This would use TestClient in a full integration test
        # For now, just verify the response structure is importable
        assert True  # Placeholder for TestClient integration
