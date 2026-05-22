"""
Tests for discovery answer validation and infrastructure mapping.

These tests verify that:
1. Valid answers pass validation
2. Invalid/placeholder answers are rejected with helpful messages
3. Infrastructure mapping is deterministic and correct
"""

import pytest
from backend.schemas.discovery import DiscoveryAnswers, RiskAppetite, TechnicalCapability
from backend.services.infrastructure import classify_workload, map_infrastructure


# ═══════════════════════════════════════════════
# Discovery Answer Validation Tests
# ═══════════════════════════════════════════════

class TestDiscoveryValidation:
    """Test that Pydantic catches bad answers before they reach Gemini."""

    def test_valid_answers_pass(self):
        """A complete, realistic set of answers should validate successfully."""
        answers = DiscoveryAnswers(
            organisation_and_bottleneck=(
                "We're a council processing 400 planning applications monthly, "
                "each taking 3 hours to review and route manually."
            ),
            data_assets="PDFs of all applications going back 10 years, SQL database tracking decisions",
            value_of_improvement="About £80,000 per year — roughly 2 full-time officers",
            risk_appetite=RiskAppetite.quick_win,
            technical_capability=TechnicalCapability.needs_support,
        )
        assert answers.organisation_and_bottleneck is not None
        assert answers.risk_appetite == RiskAppetite.quick_win

    def test_short_bottleneck_rejected(self):
        """Answers that are too short to be useful should fail."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            DiscoveryAnswers(
                organisation_and_bottleneck="We do stuff",  # Too short (min 20 chars)
                data_assets="spreadsheets",
                value_of_improvement="£50k",
                risk_appetite=RiskAppetite.quick_win,
                technical_capability=TechnicalCapability.internal_team,
            )

    def test_placeholder_bottleneck_rejected(self):
        """N/A, test, and other placeholders should be rejected."""
        with pytest.raises(Exception):
            DiscoveryAnswers(
                organisation_and_bottleneck="N/A — this is just a placeholder test answer",
                data_assets="spreadsheets and databases",
                value_of_improvement="£50k per year",
                risk_appetite=RiskAppetite.quick_win,
                technical_capability=TechnicalCapability.internal_team,
            )

    def test_no_data_rejected(self):
        """If they say they have no data, we can't build AI products."""
        with pytest.raises(Exception):
            DiscoveryAnswers(
                organisation_and_bottleneck="We are a logistics company with 200 delivery drivers and slow routing",
                data_assets="none",
                value_of_improvement="£100k",
                risk_appetite=RiskAppetite.strategic,
                technical_capability=TechnicalCapability.needs_support,
            )

    def test_zero_value_rejected(self):
        """Zero value means the brief can't quantify impact."""
        with pytest.raises(Exception):
            DiscoveryAnswers(
                organisation_and_bottleneck="We are a logistics company with 200 delivery drivers and slow routing",
                data_assets="GPS data from all vehicles, delivery manifests in Excel",
                value_of_improvement="nothing",
                risk_appetite=RiskAppetite.quick_win,
                technical_capability=TechnicalCapability.internal_team,
            )

    def test_extra_fields_rejected(self):
        """Unexpected fields should be rejected (security measure)."""
        with pytest.raises(Exception):
            DiscoveryAnswers(
                organisation_and_bottleneck="We are a logistics company with 200 delivery drivers and slow routing",
                data_assets="GPS data from all vehicles",
                value_of_improvement="£100k",
                risk_appetite=RiskAppetite.quick_win,
                technical_capability=TechnicalCapability.internal_team,
                secret_field="injection attempt",  # This should fail
            )


# ═══════════════════════════════════════════════
# Infrastructure Mapping Tests
# ═══════════════════════════════════════════════

class TestInfrastructureMapping:
    """Test that Python maps workloads to the correct DataVita facility."""

    def test_council_gets_dv1(self):
        """Public sector organisations should get sovereign hosting at DV1."""
        workload = classify_workload(
            "We're a council processing planning applications for citizens"
        )
        assert workload == "public_sector"
        recommendation = map_infrastructure(workload)
        assert "DV1" in recommendation.facility

    def test_nhs_gets_dv1(self):
        """NHS trusts need sovereign Scottish hosting."""
        workload = classify_workload(
            "We're an NHS health board running 14 hospitals with patient records"
        )
        assert workload == "public_sector"
        recommendation = map_infrastructure(workload)
        assert "DV1" in recommendation.facility

    def test_gpu_training_gets_coreweave(self):
        """AI training workloads should get DV1 + CoreWeave GPU."""
        workload = classify_workload(
            "We need to train a machine learning model on medical imaging data"
        )
        assert workload == "gpu_intensive"
        recommendation = map_infrastructure(workload)
        assert "CoreWeave" in recommendation.facility

    def test_fintech_gets_dv2(self):
        """Financial services in Glasgow should get DV2 for low latency."""
        workload = classify_workload(
            "We're a financial services fintech company needing real-time trading data processing"
        )
        assert workload == "city_facing"
        recommendation = map_infrastructure(workload)
        assert "DV2" in recommendation.facility

    def test_general_defaults_to_dv1(self):
        """Unknown workload types default to DV1 — safest option."""
        workload = classify_workload(
            "We sell artisan cheese online and want to improve our business"
        )
        assert workload == "general"
        recommendation = map_infrastructure(workload)
        assert "DV1" in recommendation.facility

    def test_mapping_is_deterministic(self):
        """Same input must always produce same output. No randomness."""
        text = "council planning applications for citizens and residents"
        results = [classify_workload(text) for _ in range(100)]
        assert len(set(results)) == 1, "Infrastructure mapping must be deterministic"


# ═══════════════════════════════════════════════
# Lead Capture Schema Tests (v1.1)
# ═══════════════════════════════════════════════

class TestLeadCaptureSchema:
    """Test that lead capture validates contact data correctly."""

    def test_valid_lead_passes(self):
        """A complete, valid lead should validate successfully."""
        from backend.schemas.lead import LeadCaptureRequest
        lead = LeadCaptureRequest(
            name="Jane Smith",
            email="jane.smith@fife.gov.uk",
            organisation="Fife Council",
            brief_summary="Fife Council processes 400 planning applications monthly.",
            infrastructure_recommended="DV1 Lanarkshire",
        )
        assert lead.name == "Jane Smith"
        assert lead.email == "jane.smith@fife.gov.uk"

    def test_invalid_email_rejected(self):
        """Malformed email addresses must be rejected."""
        from backend.schemas.lead import LeadCaptureRequest
        with pytest.raises(Exception):
            LeadCaptureRequest(
                name="Jane Smith",
                email="not-an-email",
                organisation="Fife Council",
            )

    def test_name_too_short_rejected(self):
        """A single character name should be rejected."""
        from backend.schemas.lead import LeadCaptureRequest
        with pytest.raises(Exception):
            LeadCaptureRequest(
                name="J",
                email="jane@fife.gov.uk",
                organisation="Fife Council",
            )

    def test_optional_fields_are_optional(self):
        """brief_summary and infrastructure_recommended are not required."""
        from backend.schemas.lead import LeadCaptureRequest
        lead = LeadCaptureRequest(
            name="Alex Brown",
            email="alex@example.com",
            organisation="NHS Lothian",
        )
        assert lead.brief_summary is None
        assert lead.infrastructure_recommended is None

    def test_extra_fields_rejected(self):
        """Unexpected fields must be rejected (security measure)."""
        from backend.schemas.lead import LeadCaptureRequest
        with pytest.raises(Exception):
            LeadCaptureRequest(
                name="Jane Smith",
                email="jane@fife.gov.uk",
                organisation="Fife Council",
                injection_field="DROP TABLE leads;",
            )
