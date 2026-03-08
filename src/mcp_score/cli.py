"""CLI entry point for mcp-score.

Usage:
    mcp-score http://localhost:3000/mcp
    mcp-score stdio -- python my_server.py
    mcp-score github:owner/repo
    mcp-score http://localhost:3000/mcp --repo github:myorg/server
"""

from __future__ import annotations

import sys

import click

from . import __version__

GRADE_ORDER = {"A+": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "": 0}


def _check_threshold(grade: str, threshold: str) -> bool:
    """Return True if grade meets or exceeds threshold."""
    return GRADE_ORDER.get(grade, 0) >= GRADE_ORDER.get(threshold, 0)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="mcp-score")
@click.argument("target")
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
@click.option("--repo", default=None, help="GitHub repo URL for static analysis.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["terminal", "json", "markdown"], case_sensitive=False),
    default="terminal",
    help="Output format.",
)
@click.option("--verbose", is_flag=True, help="Show individual check details.")
@click.option(
    "--fail-below",
    default=None,
    type=click.Choice(["A+", "A", "B", "C", "D", "F"], case_sensitive=False),
    help="Exit with code 1 if score is below GRADE.",
)
@click.option("--timeout", default=30, type=int, help="Probe timeout in seconds.")
@click.option(
    "--output",
    "-o",
    "output_path",
    default=None,
    type=click.Path(),
    help="Save report to a file (markdown format).",
)
def main(
    target: str,
    extra_args: tuple[str, ...],
    repo: str | None,
    output_format: str,
    verbose: bool,
    fail_below: str | None,
    timeout: int,
    output_path: str | None,
) -> None:
    """Score an MCP server's quality.

    TARGET can be:

    \b
      http://localhost:3000/mcp        Score a running HTTP server
      stdio -- python my_server.py     Score via stdio transport
      github:owner/repo                Score from GitHub repo (static only)
    """
    from .runner import run_score, ScoreError

    # Build stdio command from extra_args if target is "stdio"
    stdio_command: list[str] | None = None
    if target.lower() == "stdio":
        # Everything after "--" is the command
        args = list(extra_args)
        if args and args[0] == "--":
            args = args[1:]
        if not args:
            click.echo("Error: stdio target requires a command after '--'", err=True)
            click.echo("Example: mcp-score stdio -- python my_server.py", err=True)
            sys.exit(2)
        # Warn if CLI options appear after -- (they get passed to the server, not mcp-score)
        cli_flags = {"--format", "--verbose", "--repo", "--fail-below", "--timeout", "--output", "-o"}
        swallowed = [a for a in args if a in cli_flags]
        if swallowed:
            click.echo(
                f"Warning: {', '.join(swallowed)} after '--' will be passed to the server, "
                f"not mcp-score. Place options before 'stdio --'.",
                err=True,
            )
        stdio_command = args

    try:
        result = run_score(
            target=target,
            stdio_command=stdio_command,
            repo_url=repo,
            timeout=timeout,
        )
    except ScoreError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)

    # Format output
    if output_format == "json":
        from .formatters.json_fmt import format_json

        click.echo(format_json(result, target=target))
    elif output_format == "markdown":
        from .formatters.markdown import format_markdown

        click.echo(format_markdown(result, target=target))
    else:
        from .formatters.terminal import format_terminal

        click.echo(format_terminal(result, target=target, verbose=verbose))

    # Save to file
    if output_path:
        from .formatters.markdown import format_markdown

        report = format_markdown(result, target=target)
        with open(output_path, "w") as f:
            f.write(report)
            f.write("\n")
        click.echo(f"Report saved to {output_path}", err=True)

    # Check threshold
    if fail_below:
        if result.composite_score is None:
            click.echo(f"Warning: No score computed, cannot check --fail-below {fail_below}", err=True)
            sys.exit(2)
        if not _check_threshold(result.grade, fail_below):
            sys.exit(1)
