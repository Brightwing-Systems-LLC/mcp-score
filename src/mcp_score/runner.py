"""Pipeline orchestration — runs probes and computes scores.

Parses target types and dispatches to the appropriate probe functions
from mcp-scoring-engine.
"""

from __future__ import annotations

import re

from mcp_scoring_engine import (
    DeepProbeResult,
    ReliabilityData,
    ScoreResult,
    ServerInfo,
    StaticAnalysis,
    compute_score,
)
from mcp_scoring_engine.probes.github_client import GitHubRateLimitExhausted
from mcp_scoring_engine.probes.health import PROBE_TIMEOUT
from mcp_scoring_engine.probes.protocol import DEEP_PROBE_TIMEOUT


class ScoreError(Exception):
    """Raised when scoring fails due to invalid input or connection errors."""

    pass


def _parse_github_ref(ref: str) -> str:
    """Convert 'github:owner/repo' or URL to a full GitHub URL."""
    if ref.startswith("github:"):
        owner_repo = ref[len("github:"):]
        return f"https://github.com/{owner_repo}"
    if "github.com/" in ref:
        return ref
    raise ScoreError(f"Invalid GitHub reference: {ref}")


def _is_http_target(target: str) -> bool:
    return target.startswith("http://") or target.startswith("https://")


def _is_github_target(target: str) -> bool:
    return target.startswith("github:")


def _is_stdio_target(target: str) -> bool:
    return target.lower() == "stdio"


def _build_server_info(
    target: str,
    *,
    stdio_command: list[str] | None = None,
    repo_url: str | None = None,
    deep_probe: DeepProbeResult | None = None,
    static_result: StaticAnalysis | None = None,
) -> ServerInfo:
    """Build a ServerInfo from available data."""
    info = ServerInfo()

    if _is_http_target(target):
        info.remote_endpoint_url = target
        info.is_remote = True
    elif _is_stdio_target(target):
        info.is_remote = False
        if stdio_command:
            info.registry_metadata["transport"] = "stdio"
    elif _is_github_target(target):
        info.repo_url = _parse_github_ref(target)
        info.is_remote = True

    if repo_url:
        info.repo_url = _parse_github_ref(repo_url)

    # Extract name — prefer server-reported name from probe
    if deep_probe and deep_probe.server_name:
        info.name = deep_probe.server_name

    if not info.name:
        if _is_github_target(target):
            ref = target[len("github:"):]
            if "/" in ref:
                info.name = ref.split("/")[-1]
        elif _is_http_target(target):
            match = re.search(r"https?://([^:/]+)", target)
            if match:
                info.name = match.group(1)
        elif stdio_command:
            # Use the main command/package name, skip flags and options
            for arg in stdio_command:
                if not arg.startswith("-"):
                    info.name = arg.split("/")[-1]
                    break
            if not info.name:
                info.name = "stdio-server"

    # Enrich from static analysis
    if static_result and static_result.last_commit_at:
        info.last_commit_at = static_result.last_commit_at

    # Enrich from deep probe tools
    if deep_probe and deep_probe.tools_count:
        info.registry_metadata.setdefault("env_vars", [])

    return info


def run_score(
    target: str,
    *,
    stdio_command: list[str] | None = None,
    repo_url: str | None = None,
    timeout: int = 30,
) -> ScoreResult:
    """Run all applicable probes and compute score.

    1. Parse target type (HTTP URL, stdio command, github ref)
    2. Run applicable probes (deep probe for HTTP/stdio, static for github)
    3. Build ServerInfo from available data
    4. Call compute_score()
    5. Return ScoreResult
    """
    deep_probe: DeepProbeResult | None = None
    static_result: StaticAnalysis | None = None
    reliability: ReliabilityData | None = None

    # Determine what to run based on target type
    run_deep = _is_http_target(target) or _is_stdio_target(target)
    run_static = _is_github_target(target) or (repo_url is not None)

    # ── Deep probe ────────────────────────────────────────────────────
    if run_deep:
        if _is_http_target(target):
            from mcp_scoring_engine.probes.protocol import deep_probe_server

            deep_probe = deep_probe_server(target)
        elif _is_stdio_target(target):
            if not stdio_command:
                raise ScoreError("stdio target requires a command (after '--')")
            from mcp_scoring_engine.probes.protocol import deep_probe_server_stdio

            deep_probe = deep_probe_server_stdio(stdio_command)

        # Build reliability from probe latency (single run)
        if deep_probe and deep_probe.is_reachable and deep_probe.connection_ms is not None:
            reliability = ReliabilityData(
                latency_p50_ms=deep_probe.connection_ms,
                probe_count=1,
            )

    # ── Static analysis ───────────────────────────────────────────────
    if run_static:
        from mcp_scoring_engine.probes.static import analyze_repo

        github_url = repo_url or target
        try:
            resolved = _parse_github_ref(github_url)
        except ScoreError:
            if not run_deep:
                raise
            resolved = None

        if resolved:
            try:
                static_result = analyze_repo(resolved)
            except GitHubRateLimitExhausted:
                if not run_deep:
                    raise ScoreError(
                        "GitHub API rate limit exhausted. "
                        "Set GITHUB_TOKEN env var for 5,000 req/hr (vs 60 unauthenticated)."
                    )
                # If we also have a deep probe, continue without static analysis
                import sys

                print(
                    "Warning: GitHub API rate limit exhausted, skipping static analysis. "
                    "Set GITHUB_TOKEN for higher limits.",
                    file=sys.stderr,
                )

    # ── Build server info and score ───────────────────────────────────
    server_info = _build_server_info(
        target,
        stdio_command=stdio_command,
        repo_url=repo_url,
        deep_probe=deep_probe,
        static_result=static_result,
    )

    result = compute_score(
        server_info,
        static_result=static_result,
        deep_probe=deep_probe,
        reliability=reliability,
    )

    return result
