"""Shared test fixtures for mcp-score tests."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from mcp_scoring_engine import (
    DeepProbeResult,
    ReliabilityData,
    ScoreResult,
    ServerInfo,
    StaticAnalysis,
    Flag,
)


@pytest.fixture
def sample_result() -> ScoreResult:
    """A complete ScoreResult for formatter testing."""
    return ScoreResult(
        composite_score=82,
        grade="B",
        score_type="full",
        schema_docs_score=75,
        protocol_score=90,
        reliability_score=80,
        maintenance_score=68,
        security_score=85,
        flags=[
            Flag(
                key="STALE_PROJECT",
                severity="warning",
                label="Stale Project",
                description="No commits in over 12 months.",
            ),
        ],
        badges={
            "schema": [{"key": "has_readme", "label": "README", "level": "good"}],
            "protocol": [{"key": "reachable", "label": "Reachable", "level": "good"}],
            "reliability": [],
            "maintenance": [],
            "security": [],
        },
        category="devtools",
        targets=["GitHub"],
        publisher="acme-corp",
        verified_publisher=False,
        deep_probe=DeepProbeResult(
            is_reachable=True,
            connection_ms=45,
            initialize_ms=120,
            ping_ms=30,
            tools_list_ms=80,
            tools_count=5,
            schema_valid=True,
            schema_issues=[],
            error_handling_score=87,
            error_handling_details={"tests_passed": 3, "tests_total": 3},
            fuzz_score=75,
            fuzz_details={"tests_passed": 6, "tests_total": 8},
        ),
        static_analysis=StaticAnalysis(
            schema_completeness=85,
            description_quality=78,
            documentation_coverage=72,
            maintenance_pulse=80,
            dependency_health=75,
            license_clarity=100,
            version_hygiene=65,
        ),
        reliability_data=ReliabilityData(
            latency_p50_ms=45,
            probe_count=1,
        ),
        server_info=ServerInfo(
            name="awesome-mcp-server",
            repo_url="https://github.com/acme-corp/awesome-mcp-server",
        ),
    )


@pytest.fixture
def partial_result() -> ScoreResult:
    """A partial ScoreResult with limited data."""
    return ScoreResult(
        composite_score=65,
        grade="",
        score_type="partial",
        security_score=65,
        flags=[],
        badges={"schema": [], "protocol": [], "reliability": [], "maintenance": [], "security": []},
        server_info=ServerInfo(name="minimal-server"),
    )


@pytest.fixture
def empty_result() -> ScoreResult:
    """A ScoreResult with no data."""
    return ScoreResult(
        server_info=ServerInfo(),
    )
