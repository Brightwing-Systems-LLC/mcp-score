"""Markdown output formatter for score results.

Suitable for PR comments, documentation, or piping to a file.
"""

from __future__ import annotations

from mcp_scoring_engine import ScoreResult


def format_markdown(result: ScoreResult, *, target: str = "") -> str:
    """Format a ScoreResult as markdown."""
    lines = []

    name = ""
    if result.server_info:
        name = result.server_info.name or target
    else:
        name = target

    lines.append(f"# MCP Server Score Report: {name}")
    lines.append("")

    if result.composite_score is not None:
        grade_str = result.grade or "—"
        lines.append(f"**Overall Score: {result.composite_score}/100 (Grade: {grade_str})**")
        if result.score_type == "partial":
            lines.append("*Partial score — limited data available*")
    else:
        lines.append("*No score computed — insufficient data*")

    lines.append("")

    # Category table
    is_enhanced = result.score_type == "enhanced"
    lines.append("| Category | Score | Weight |")
    lines.append("|---|---:|---:|")

    if is_enhanced:
        categories = [
            ("Schema Quality", result.schema_quality_score, "20%"),
            ("Protocol Compliance", result.protocol_score, "18%"),
            ("Reliability", result.reliability_score, "18%"),
            ("Docs & Maintenance", result.docs_maintenance_score, "12%"),
            ("Security & Permissions", result.security_score, "17%"),
            ("Agent Usability", result.agent_usability_score, "15%"),
        ]
    else:
        categories = [
            ("Schema Quality", result.schema_quality_score, "25%"),
            ("Protocol Compliance", result.protocol_score, "20%"),
            ("Reliability", result.reliability_score, "20%"),
            ("Docs & Maintenance", result.docs_maintenance_score, "15%"),
            ("Security & Permissions", result.security_score, "20%"),
        ]

    for label, score, weight in categories:
        score_str = str(score) if score is not None else "—"
        lines.append(f"| {label} | {score_str} | {weight} |")

    # Flags
    if result.flags:
        lines.append("")
        lines.append("## Flags")
        lines.append("")
        for flag in result.flags:
            icon = "🔴" if flag.severity == "critical" else "🟡"
            lines.append(f"- {icon} **{flag.key}**: {flag.description}")

    # Probe summary
    if result.deep_probe and result.deep_probe.is_reachable:
        probe = result.deep_probe
        lines.append("")
        lines.append("## Probe Results")
        lines.append("")
        if probe.tools_count is not None:
            lines.append(f"- **Tools Found**: {probe.tools_count}")
        if probe.schema_valid is not None:
            lines.append(f"- **Schema Valid**: {'Yes' if probe.schema_valid else 'No'}")
        if probe.error_handling_score is not None:
            lines.append(f"- **Error Handling**: {probe.error_handling_score}/100")
        if probe.fuzz_score is not None:
            lines.append(f"- **Fuzz Resilience**: {probe.fuzz_score}/100")
        if probe.connection_ms is not None:
            lines.append(f"- **Latency**: {probe.connection_ms}ms")

    # Footer with subtle PatchworkMCP CTA
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("Improvement guides: [mcpscoreboard.com/build](https://mcpscoreboard.com/build)")
    lines.append("")
    lines.append(
        "Continuous monitoring & agent feedback: "
        "[patchworkmcp.com](https://patchworkmcp.com)"
    )

    return "\n".join(lines)
