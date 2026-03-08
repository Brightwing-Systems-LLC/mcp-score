"""Tests for output formatters."""

import json

from mcp_scoring_engine import ScoreResult, ServerInfo

from mcp_score.formatters.terminal import format_terminal, _grade_color, _score_color
from mcp_score.formatters.json_fmt import format_json
from mcp_score.formatters.markdown import format_markdown


class TestGradeColor:
    def test_a_plus(self):
        assert _grade_color("A+") == "green"

    def test_a(self):
        assert _grade_color("A") == "green"

    def test_b(self):
        assert _grade_color("B") == "cyan"

    def test_c(self):
        assert _grade_color("C") == "yellow"

    def test_d(self):
        assert _grade_color("D") == "red"

    def test_f(self):
        assert _grade_color("F") == "bold red"

    def test_empty(self):
        assert _grade_color("") == "dim"


class TestScoreColor:
    def test_high(self):
        assert _score_color(95) == "green"

    def test_good(self):
        assert _score_color(75) == "cyan"

    def test_mid(self):
        assert _score_color(60) == "yellow"

    def test_low(self):
        assert _score_color(45) == "red"

    def test_very_low(self):
        assert _score_color(20) == "bold red"

    def test_none(self):
        assert _score_color(None) == "dim"


class TestTerminalFormatter:
    def test_full_result(self, sample_result):
        output = format_terminal(sample_result, target="http://localhost:3000/mcp")
        assert "MCP Server Score Report" in output
        assert "awesome-mcp-server" in output
        assert "82" in output
        assert "Schema Quality" in output
        assert "Protocol Compliance" in output

    def test_partial_result(self, partial_result):
        output = format_terminal(partial_result)
        assert "No score computed" in output

    def test_empty_result(self, empty_result):
        output = format_terminal(empty_result)
        assert "No score computed" in output

    def test_target_as_name(self):
        result = ScoreResult(
            composite_score=70,
            grade="B",
            server_info=ServerInfo(),
        )
        output = format_terminal(result, target="http://example.com")
        assert "http://example.com" in output

    def test_flags_shown(self, sample_result):
        output = format_terminal(sample_result)
        assert "STALE_PROJECT" in output

    def test_probe_details_shown(self, sample_result):
        output = format_terminal(sample_result)
        assert "Tools Found: 5" in output
        assert "Schema Valid" in output
        assert "45ms" in output

    def test_verbose_probe_timing(self, sample_result):
        output = format_terminal(sample_result, verbose=True)
        assert "Probe Timing" in output
        assert "Connect: 45ms" in output
        assert "Initialize: 120ms" in output

    def test_verbose_static_analysis(self, sample_result):
        output = format_terminal(sample_result, verbose=True)
        assert "Static Analysis" in output
        assert "Schema Completeness: 85/100" in output

    def test_footer_has_cta(self, sample_result):
        output = format_terminal(sample_result)
        assert "mcpscoreboard.com" in output or "patchworkmcp.com" in output

    def test_enhanced_weights(self):
        result = ScoreResult(
            composite_score=80,
            grade="B",
            score_type="enhanced",
            schema_quality_score=75,
            protocol_score=85,
            reliability_score=80,
            docs_maintenance_score=70,
            security_score=90,
            agent_usability_score=78,
            server_info=ServerInfo(name="test"),
        )
        output = format_terminal(result)
        assert "Agent Usability" in output
        assert "15%" in output


class TestJsonFormatter:
    def test_valid_json(self, sample_result):
        output = format_json(sample_result, target="http://localhost:3000/mcp")
        data = json.loads(output)
        assert data["score"]["composite"] == 82
        assert data["score"]["grade"] == "B"

    def test_target_included(self, sample_result):
        output = format_json(sample_result, target="http://example.com")
        data = json.loads(output)
        assert data["target"] == "http://example.com"

    def test_version_included(self, sample_result):
        output = format_json(sample_result)
        data = json.loads(output)
        assert "version" in data
        assert data["version"] == "0.1.0"

    def test_timestamp_included(self, sample_result):
        output = format_json(sample_result)
        data = json.loads(output)
        assert "timestamp" in data

    def test_categories(self, sample_result):
        output = format_json(sample_result)
        data = json.loads(output)
        cats = data["score"]["categories"]
        assert cats["schema_quality"] == 75
        assert cats["protocol"] == 90
        assert cats["reliability"] == 80
        assert cats["docs_maintenance"] == 68
        assert cats["security"] == 85

    def test_agent_usability_included_when_present(self):
        result = ScoreResult(
            composite_score=80,
            grade="B",
            score_type="enhanced",
            schema_quality_score=75,
            agent_usability_score=82,
            server_info=ServerInfo(name="test"),
        )
        output = format_json(result)
        data = json.loads(output)
        assert data["score"]["categories"]["agent_usability"] == 82

    def test_agent_usability_omitted_when_none(self, sample_result):
        output = format_json(sample_result)
        data = json.loads(output)
        assert "agent_usability" not in data["score"]["categories"]

    def test_flags(self, sample_result):
        output = format_json(sample_result)
        data = json.loads(output)
        assert len(data["flags"]) == 1
        assert data["flags"][0]["key"] == "STALE_PROJECT"

    def test_probe_data(self, sample_result):
        output = format_json(sample_result)
        data = json.loads(output)
        assert data["probe"]["is_reachable"] is True
        assert data["probe"]["tools_count"] == 5
        assert data["probe"]["schema_valid"] is True

    def test_static_analysis(self, sample_result):
        output = format_json(sample_result)
        data = json.loads(output)
        assert data["static_analysis"]["schema_completeness"] == 85

    def test_reliability(self, sample_result):
        output = format_json(sample_result)
        data = json.loads(output)
        assert data["reliability"]["latency_p50_ms"] == 45
        assert data["reliability"]["probe_count"] == 1

    def test_empty_result(self, empty_result):
        output = format_json(empty_result)
        data = json.loads(output)
        assert data["score"]["composite"] is None
        assert data["score"]["grade"] == ""

    def test_no_probe(self):
        result = ScoreResult(
            composite_score=50,
            grade="C",
            server_info=ServerInfo(name="test"),
        )
        output = format_json(result)
        data = json.loads(output)
        assert "probe" not in data

    def test_cta_included(self, sample_result):
        output = format_json(sample_result)
        data = json.loads(output)
        assert "cta" in data
        assert "message" in data["cta"]
        assert "url" in data["cta"]
        assert "label" in data["cta"]
        assert data["cta"]["url"].startswith("https://")


class TestMarkdownFormatter:
    def test_header(self, sample_result):
        output = format_markdown(sample_result, target="http://localhost:3000/mcp")
        assert "# MCP Server Score Report: awesome-mcp-server" in output

    def test_overall_score(self, sample_result):
        output = format_markdown(sample_result)
        assert "82/100" in output
        assert "Grade: B" in output

    def test_category_table(self, sample_result):
        output = format_markdown(sample_result)
        assert "| Category | Score | Weight |" in output
        assert "Schema Quality" in output
        assert "75" in output

    def test_flags(self, sample_result):
        output = format_markdown(sample_result)
        assert "STALE_PROJECT" in output

    def test_probe_results(self, sample_result):
        output = format_markdown(sample_result)
        assert "## Probe Results" in output
        assert "Tools Found**: 5" in output

    def test_footer_has_cta(self, sample_result):
        output = format_markdown(sample_result)
        assert "mcpscoreboard.com" in output or "patchworkmcp.com" in output

    def test_partial_result(self, partial_result):
        output = format_markdown(partial_result)
        assert "No score computed" in output

    def test_empty_result(self, empty_result):
        output = format_markdown(empty_result)
        assert "No score computed" in output

    def test_target_as_name(self):
        result = ScoreResult(server_info=ServerInfo())
        output = format_markdown(result, target="http://example.com")
        assert "http://example.com" in output

    def test_no_flags(self):
        result = ScoreResult(
            composite_score=90,
            grade="A",
            flags=[],
            server_info=ServerInfo(name="test"),
        )
        output = format_markdown(result)
        assert "## Flags" not in output

    def test_enhanced_weights(self):
        result = ScoreResult(
            composite_score=80,
            grade="B",
            score_type="enhanced",
            schema_quality_score=75,
            protocol_score=85,
            reliability_score=80,
            docs_maintenance_score=70,
            security_score=90,
            agent_usability_score=78,
            server_info=ServerInfo(name="test"),
        )
        output = format_markdown(result)
        assert "Agent Usability" in output
        assert "15%" in output
