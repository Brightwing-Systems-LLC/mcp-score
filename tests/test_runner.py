"""Tests for the scoring pipeline runner."""

from unittest.mock import patch, MagicMock

import pytest

from mcp_scoring_engine import DeepProbeResult, StaticAnalysis, ScoreResult
from mcp_score.runner import (
    ScoreError,
    _parse_github_ref,
    _is_http_target,
    _is_github_target,
    _is_stdio_target,
    _build_server_info,
    run_score,
)


class TestTargetParsing:
    def test_http_target(self):
        assert _is_http_target("http://localhost:3000/mcp") is True
        assert _is_http_target("https://api.example.com/mcp") is True
        assert _is_http_target("github:owner/repo") is False
        assert _is_http_target("stdio") is False

    def test_github_target(self):
        assert _is_github_target("github:owner/repo") is True
        assert _is_github_target("http://example.com") is False

    def test_stdio_target(self):
        assert _is_stdio_target("stdio") is True
        assert _is_stdio_target("STDIO") is True
        assert _is_stdio_target("http://example.com") is False


class TestParseGithubRef:
    def test_short_form(self):
        assert _parse_github_ref("github:owner/repo") == "https://github.com/owner/repo"

    def test_full_url(self):
        url = "https://github.com/owner/repo"
        assert _parse_github_ref(url) == url

    def test_invalid(self):
        with pytest.raises(ScoreError):
            _parse_github_ref("not-a-github-ref")


class TestBuildServerInfo:
    def test_http_target(self):
        info = _build_server_info("http://localhost:3000/mcp")
        assert info.remote_endpoint_url == "http://localhost:3000/mcp"
        assert info.is_remote is True

    def test_stdio_target(self):
        info = _build_server_info("stdio", stdio_command=["python", "server.py"])
        assert info.is_remote is False

    def test_github_target(self):
        info = _build_server_info("github:myorg/my-server")
        assert info.repo_url == "https://github.com/myorg/my-server"
        assert info.name == "my-server"

    def test_with_repo_url(self):
        info = _build_server_info(
            "http://localhost:3000/mcp",
            repo_url="github:myorg/server",
        )
        assert info.repo_url == "https://github.com/myorg/server"
        assert info.remote_endpoint_url == "http://localhost:3000/mcp"


class TestRunScore:
    @patch("mcp_scoring_engine.probes.protocol.deep_probe_server")
    def test_http_mode(self, mock_probe):
        mock_probe.return_value = DeepProbeResult(
            is_reachable=True,
            connection_ms=50,
            tools_count=3,
            schema_valid=True,
            error_handling_score=80,
        )
        result = run_score("http://localhost:3000/mcp")
        assert isinstance(result, ScoreResult)
        assert result.protocol_score is not None
        mock_probe.assert_called_once_with("http://localhost:3000/mcp")

    @patch("mcp_scoring_engine.probes.protocol.deep_probe_server_stdio")
    def test_stdio_mode(self, mock_probe):
        mock_probe.return_value = DeepProbeResult(
            is_reachable=True,
            connection_ms=30,
            tools_count=5,
            schema_valid=True,
            error_handling_score=90,
        )
        result = run_score("stdio", stdio_command=["python", "server.py"])
        assert isinstance(result, ScoreResult)
        mock_probe.assert_called_once_with(["python", "server.py"])

    def test_stdio_without_command(self):
        with pytest.raises(ScoreError, match="requires a command"):
            run_score("stdio")

    @patch("mcp_scoring_engine.probes.static.analyze_repo")
    def test_github_mode(self, mock_analyze):
        mock_analyze.return_value = StaticAnalysis(
            schema_completeness=80,
            description_quality=70,
            documentation_coverage=60,
            maintenance_pulse=75,
            dependency_health=65,
            license_clarity=100,
            version_hygiene=50,
        )
        result = run_score("github:owner/repo")
        assert isinstance(result, ScoreResult)
        assert result.schema_quality_score is not None
        assert result.protocol_score is None
        mock_analyze.assert_called_once_with("https://github.com/owner/repo")

    @patch("mcp_scoring_engine.probes.static.analyze_repo")
    @patch("mcp_scoring_engine.probes.protocol.deep_probe_server")
    def test_combined_mode(self, mock_probe, mock_analyze):
        mock_probe.return_value = DeepProbeResult(
            is_reachable=True, connection_ms=50, tools_count=3,
            schema_valid=True, error_handling_score=80,
        )
        mock_analyze.return_value = StaticAnalysis(
            schema_completeness=80, description_quality=70,
            documentation_coverage=60,
        )
        result = run_score(
            "http://localhost:3000/mcp",
            repo_url="github:owner/repo",
        )
        assert result.protocol_score is not None
        assert result.schema_quality_score is not None

    @patch("mcp_scoring_engine.probes.protocol.deep_probe_server")
    def test_reliability_from_probe(self, mock_probe):
        mock_probe.return_value = DeepProbeResult(
            is_reachable=True, connection_ms=150,
        )
        result = run_score("http://localhost:3000/mcp")
        assert result.reliability_data is not None
        assert result.reliability_data.latency_p50_ms == 150
        assert result.reliability_data.probe_count == 1
