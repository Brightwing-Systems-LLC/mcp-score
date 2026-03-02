"""Tests for CLI argument parsing and dispatch."""

from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from mcp_score.cli import main, _check_threshold, GRADE_ORDER


class TestCheckThreshold:
    def test_a_plus_meets_a_plus(self):
        assert _check_threshold("A+", "A+") is True

    def test_a_meets_b(self):
        assert _check_threshold("A", "B") is True

    def test_b_fails_a(self):
        assert _check_threshold("B", "A") is False

    def test_f_fails_everything(self):
        assert _check_threshold("F", "A+") is False
        assert _check_threshold("F", "F") is True

    def test_empty_grade_fails(self):
        assert _check_threshold("", "B") is False


class TestCLIHelp:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Score an MCP server" in result.output
        assert "--format" in result.output
        assert "--fail-below" in result.output

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "mcp-score" in result.output


class TestCLIStdioValidation:
    def test_stdio_without_command(self):
        runner = CliRunner()
        result = runner.invoke(main, ["stdio"])
        assert result.exit_code == 2

    def test_stdio_with_empty_args(self):
        runner = CliRunner()
        result = runner.invoke(main, ["stdio", "--"])
        assert result.exit_code == 2


class TestCLIWithMockedRunner:
    def _make_result(self, score=82, grade="B"):
        from mcp_scoring_engine import ScoreResult, ServerInfo
        return ScoreResult(
            composite_score=score,
            grade=grade,
            score_type="full",
            schema_docs_score=75,
            protocol_score=90,
            reliability_score=80,
            maintenance_score=68,
            security_score=85,
            flags=[],
            badges={"schema": [], "protocol": [], "reliability": [], "maintenance": [], "security": []},
            server_info=ServerInfo(name="test"),
        )

    @patch("mcp_score.runner.run_score")
    def test_http_target_terminal(self, mock_run):
        mock_run.return_value = self._make_result()
        runner = CliRunner()
        result = runner.invoke(main, ["http://localhost:3000/mcp"])
        assert result.exit_code == 0
        assert "82" in result.output

    @patch("mcp_score.runner.run_score")
    def test_http_target_json(self, mock_run):
        mock_run.return_value = self._make_result()
        runner = CliRunner()
        result = runner.invoke(main, ["http://localhost:3000/mcp", "--format", "json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert data["score"]["composite"] == 82
        assert data["score"]["grade"] == "B"

    @patch("mcp_score.runner.run_score")
    def test_http_target_markdown(self, mock_run):
        mock_run.return_value = self._make_result()
        runner = CliRunner()
        result = runner.invoke(main, ["http://localhost:3000/mcp", "--format", "markdown"])
        assert result.exit_code == 0
        assert "82/100" in result.output
        assert "Grade: B" in result.output

    @patch("mcp_score.runner.run_score")
    def test_fail_below_passes(self, mock_run):
        mock_run.return_value = self._make_result(score=82, grade="B")
        runner = CliRunner()
        result = runner.invoke(main, ["http://localhost:3000/mcp", "--fail-below", "C"])
        assert result.exit_code == 0

    @patch("mcp_score.runner.run_score")
    def test_fail_below_fails(self, mock_run):
        mock_run.return_value = self._make_result(score=82, grade="B")
        runner = CliRunner()
        result = runner.invoke(main, ["http://localhost:3000/mcp", "--fail-below", "A"])
        assert result.exit_code == 1

    @patch("mcp_score.runner.run_score")
    def test_fail_below_no_score(self, mock_run):
        from mcp_scoring_engine import ScoreResult, ServerInfo
        mock_run.return_value = ScoreResult(server_info=ServerInfo())
        runner = CliRunner()
        result = runner.invoke(main, ["http://localhost:3000/mcp", "--fail-below", "B"])
        assert result.exit_code == 2

    @patch("mcp_score.runner.run_score")
    def test_runner_error(self, mock_run):
        from mcp_score.runner import ScoreError
        mock_run.side_effect = ScoreError("Connection failed")
        runner = CliRunner()
        result = runner.invoke(main, ["http://localhost:3000/mcp"])
        assert result.exit_code == 2
        assert "Connection failed" in result.output

    @patch("mcp_score.runner.run_score")
    def test_stdio_target(self, mock_run):
        mock_run.return_value = self._make_result()
        runner = CliRunner()
        result = runner.invoke(main, ["stdio", "--", "python", "my_server.py"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["stdio_command"] == ["python", "my_server.py"]

    @patch("mcp_score.runner.run_score")
    def test_github_target(self, mock_run):
        mock_run.return_value = self._make_result()
        runner = CliRunner()
        result = runner.invoke(main, ["github:owner/repo"])
        assert result.exit_code == 0
        mock_run.assert_called_once_with(
            target="github:owner/repo",
            stdio_command=None,
            repo_url=None,
            timeout=30,
        )

    @patch("mcp_score.runner.run_score")
    def test_repo_option(self, mock_run):
        mock_run.return_value = self._make_result()
        runner = CliRunner()
        result = runner.invoke(main, [
            "http://localhost:3000/mcp",
            "--repo", "github:owner/repo",
        ])
        assert result.exit_code == 0
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["repo_url"] == "github:owner/repo"
