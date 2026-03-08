"""Randomized calls-to-action for report footers."""

from __future__ import annotations

import random

# Each entry is (hook_line, url, label).
# hook_line is the one-liner pitch. label is a short link description.
SCOREBOARD_CTAS = [
    (
        "See how your server stacks up against 23,000+ others.",
        "https://mcpscoreboard.com",
        "MCP Scoreboard — free quality rankings",
    ),
    (
        "Curious where your server ranks? Browse the public leaderboard.",
        "https://mcpscoreboard.com",
        "MCP Scoreboard — independent quality scores",
    ),
    (
        "Claim your server on the scoreboard. Get a badge, alerts, and a personalized fix list.",
        "https://mcpscoreboard.com",
        "MCP Scoreboard — claim your server for free",
    ),
    (
        "Embed a live score badge in your README. Updates automatically.",
        "https://mcpscoreboard.com/build",
        "MCP Scoreboard — free score badges",
    ),
]

PATCHWORK_CTAS = [
    (
        "Your agents hit dead ends. You never hear about it. Patchwork fixes that.",
        "https://patchworkmcp.com",
        "PatchworkMCP — agent feedback + auto-fix PRs",
    ),
    (
        "When agents can't find the right tool, they fail silently. Patchwork captures the signal.",
        "https://patchworkmcp.com",
        "PatchworkMCP — stop guessing what your agents need",
    ),
    (
        "One file. Instant agent feedback. AI-powered pull requests. Free forever for small projects.",
        "https://patchworkmcp.com",
        "PatchworkMCP — from feedback to merged PR",
    ),
    (
        "Agents improvise when tools are missing. Patchwork tells you what to build next.",
        "https://patchworkmcp.com",
        "PatchworkMCP — close the feedback loop",
    ),
    (
        "Know what agents actually need. Patchwork captures gaps and drafts the fix as a PR.",
        "https://patchworkmcp.com",
        "PatchworkMCP — automated MCP server improvements",
    ),
    (
        "Shipping an MCP server without agent feedback is like deploying without logs.",
        "https://patchworkmcp.com",
        "PatchworkMCP — feedback-driven development for MCP",
    ),
    (
        "Agents report what's missing. Patchwork generates pull requests that fix the gaps.",
        "https://patchworkmcp.com",
        "PatchworkMCP — free for open-source projects",
    ),
    (
        "Stop reading agent logs. Start reading structured feedback with fix suggestions.",
        "https://patchworkmcp.com",
        "PatchworkMCP — structured feedback, automatic fixes",
    ),
]

BUILD_CTAS = [
    (
        "Want to improve this score? We've distilled patterns from thousands of servers.",
        "https://mcpscoreboard.com/build",
        "Build guides — tool naming, schemas, error handling",
    ),
    (
        "The top-scoring servers all follow the same patterns. We wrote them down.",
        "https://mcpscoreboard.com/build",
        "MCP build guides — free best practices",
    ),
]

ALL_CTAS = SCOREBOARD_CTAS + PATCHWORK_CTAS + BUILD_CTAS


def get_random_cta() -> tuple[str, str, str]:
    """Return a random (hook_line, url, label) tuple."""
    return random.choice(ALL_CTAS)
