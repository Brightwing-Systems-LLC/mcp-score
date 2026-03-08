"""Rich terminal output for score reports."""

from __future__ import annotations

import io

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from mcp_scoring_engine import ScoreResult


def _grade_color(grade: str) -> str:
    if grade in ("A+", "A"):
        return "green"
    elif grade == "B":
        return "cyan"
    elif grade == "C":
        return "yellow"
    elif grade == "D":
        return "red"
    elif grade == "F":
        return "bold red"
    return "dim"


def _score_color(score: int | None) -> str:
    if score is None:
        return "dim"
    if score >= 85:
        return "green"
    elif score >= 70:
        return "cyan"
    elif score >= 55:
        return "yellow"
    elif score >= 40:
        return "red"
    return "bold red"


def format_terminal(
    result: ScoreResult,
    *,
    target: str = "",
    verbose: bool = False,
) -> str:
    """Format a ScoreResult as a rich terminal report."""
    console = Console(record=True, width=60, file=io.StringIO())

    # Header
    name = ""
    if result.server_info:
        name = result.server_info.name or target
    else:
        name = target

    console.print()
    console.print(
        Panel(
            Text.from_markup(
                f"[bold]MCP Server Score Report[/bold]\n{name}"
            ),
            expand=True,
        )
    )

    # Overall score
    if result.composite_score is not None:
        grade_str = result.grade or "—"
        color = _grade_color(result.grade)
        console.print(
            f"  Overall Score:  [bold]{result.composite_score}/100[/bold]  "
            f"Grade: [{color}][bold]{grade_str}[/bold][/{color}]"
        )
        if result.score_type == "partial":
            console.print("  [dim](Partial score — limited data available)[/dim]")
    else:
        console.print("  [dim]No score computed — insufficient data[/dim]")

    console.print()

    # Category breakdown table
    is_enhanced = result.score_type == "enhanced"
    table = Table(show_header=True, header_style="bold", expand=True)
    table.add_column("Category", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Wt.", justify="right", style="dim")

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
        if score is not None:
            color = _score_color(score)
            score_str = f"[{color}]{score}[/{color}]"
        else:
            score_str = "[dim]—[/dim]"
        table.add_row(label, score_str, weight)

    console.print(table)

    # Flags
    if result.flags:
        console.print()
        console.print("  [bold]Flags:[/bold]")
        for flag in result.flags:
            icon = "[red]✗[/red]" if flag.severity == "critical" else "[yellow]⚠[/yellow]"
            console.print(f"    {icon} {flag.key} — {flag.description}")

    # Probe details
    if result.deep_probe and result.deep_probe.is_reachable:
        probe = result.deep_probe
        console.print()
        if probe.tools_count is not None:
            console.print(f"  Tools Found: {probe.tools_count}")
        if probe.schema_valid is not None:
            status = "[green]Yes[/green]" if probe.schema_valid else "[yellow]No[/yellow]"
            console.print(f"  Schema Valid: {status}")
        if probe.error_handling_score is not None:
            console.print(f"  Error Handling: {probe.error_handling_score}/100")
        if probe.connection_ms is not None:
            console.print(f"  Latency: {probe.connection_ms}ms")

    elif result.deep_probe and not result.deep_probe.is_reachable:
        console.print()
        console.print(
            f"  [red]Server unreachable[/red]: {result.deep_probe.error_message}"
        )

    # Verbose: show detailed breakdowns
    if verbose and result.deep_probe:
        probe = result.deep_probe
        console.print()
        console.print("  [bold]Probe Timing:[/bold]")
        if probe.connection_ms is not None:
            console.print(f"    Connect: {probe.connection_ms}ms")
        if probe.initialize_ms is not None:
            console.print(f"    Initialize: {probe.initialize_ms}ms")
        if probe.ping_ms is not None:
            console.print(f"    Ping: {probe.ping_ms}ms")
        if probe.tools_list_ms is not None:
            console.print(f"    tools/list: {probe.tools_list_ms}ms")

        if probe.schema_issues:
            console.print()
            console.print("  [bold]Schema Issues:[/bold]")
            for issue in probe.schema_issues:
                console.print(f"    [yellow]•[/yellow] {issue}")

        if probe.error_handling_details:
            console.print()
            console.print("  [bold]Error Handling Details:[/bold]")
            for k, v in probe.error_handling_details.items():
                if k not in ("tests_passed", "tests_total"):
                    console.print(f"    {k}: {v}")

        if probe.fuzz_score is not None:
            console.print(f"  Fuzz Score: {probe.fuzz_score}/100")

    if verbose and result.static_analysis:
        sa = result.static_analysis
        console.print()
        console.print("  [bold]Static Analysis:[/bold]")
        console.print(f"    Schema Completeness: {sa.schema_completeness}/100")
        console.print(f"    Description Quality: {sa.description_quality}/100")
        console.print(f"    Documentation Coverage: {sa.documentation_coverage}/100")
        console.print(f"    Maintenance Pulse: {sa.maintenance_pulse}/100")
        console.print(f"    Dependency Health: {sa.dependency_health}/100")
        console.print(f"    License Clarity: {sa.license_clarity}/100")
        console.print(f"    Version Hygiene: {sa.version_hygiene}/100")

    # Footer
    console.print()
    console.print("  [dim]─" * 50 + "[/dim]")
    if result.category and result.category != "other":
        console.print(f"  Category: {result.category}")
    if result.publisher:
        verified = " ✓" if result.verified_publisher else ""
        console.print(f"  Publisher: {result.publisher}{verified}")

    # Randomized CTA
    from .cta import get_random_cta

    hook, url, label = get_random_cta()
    console.print()
    console.print(f"  [bold]{hook}[/bold]")
    console.print(f"  [cyan]{url}[/cyan]")
    console.print(f"  [dim]{label}[/dim]")
    console.print()

    return console.export_text()
