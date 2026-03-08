# mcp-score

Score your MCP server's quality before publishing. A command-line tool that probes [Model Context Protocol](https://modelcontextprotocol.io) servers and produces a quality report covering schema compliance, protocol behavior, error handling, security, and more.

Built on [mcp-scoring-engine](https://pypi.org/project/mcp-scoring-engine/) — the same engine that powers the [MCP Scoreboard](https://mcpscoreboard.com).

## Installation

```bash
pip install mcp-score
```

Requires Python 3.12+.

## Quick Start

```bash
# Score a running HTTP server
mcp-score http://localhost:3000/mcp

# Score a server via stdio transport
mcp-score stdio -- python my_server.py

# Score a server via npx
mcp-score stdio -- npx -y @modelcontextprotocol/server-everything stdio

# Score a GitHub repo (static analysis only, no live probe)
mcp-score github:owner/repo

# Combine: probe a running server + analyze its source
mcp-score http://localhost:3000/mcp --repo github:owner/repo
```

## Usage

```
Usage: mcp-score [OPTIONS] TARGET [EXTRA_ARGS]...

  Score an MCP server's quality.

  TARGET can be:

    http://localhost:3000/mcp        Score a running HTTP server
    stdio -- python my_server.py     Score via stdio transport
    github:owner/repo                Score from GitHub repo (static only)

Options:
  --version                       Show the version and exit.
  --repo TEXT                     GitHub repo URL for static analysis.
  --format [terminal|json|markdown]
                                  Output format.
  --verbose                       Show individual check details.
  --fail-below [A+|A|B|C|D|F]    Exit with code 1 if score is below GRADE.
  --timeout INTEGER               Probe timeout in seconds.
  -o, --output PATH               Save report to a file (markdown format).
  -h, --help                      Show this message and exit.
```

> **Note:** When using `stdio`, all mcp-score options must come **before** the target. Everything after `--` is passed directly to the server process.
>
> ```bash
> # Correct — options before the target
> mcp-score --format json --verbose stdio -- python my_server.py
>
> # Wrong — --format and --verbose get passed to my_server.py
> mcp-score stdio -- python my_server.py --format json --verbose
> ```

## Target Types

### HTTP / HTTPS

Score a running MCP server accessible over HTTP:

```bash
mcp-score http://localhost:3000/mcp
mcp-score https://my-mcp-server.example.com/mcp
```

Runs a deep protocol probe: connection, initialization, ping, `tools/list`, schema validation, error handling tests, and fuzz testing.

### Stdio

Score a server that communicates via stdin/stdout:

```bash
mcp-score stdio -- python my_server.py
mcp-score stdio -- node dist/index.js
mcp-score stdio -- npx -y @modelcontextprotocol/server-everything stdio
```

Launches the process, runs the same deep protocol probe over stdio, then terminates the process.

### GitHub (Static Only)

Analyze a server's source code without running it:

```bash
mcp-score github:owner/repo
mcp-score github:modelcontextprotocol/servers
```

Runs static analysis via the GitHub API: schema completeness, description quality, documentation coverage, maintenance pulse, dependency health, license clarity, and version hygiene.

> **Tip:** Unauthenticated GitHub API requests are limited to 60/hour. Set `GITHUB_TOKEN` for 5,000/hour:
> ```bash
> export GITHUB_TOKEN=ghp_your_token_here
> ```

### Combined (Probe + Static)

For the most complete score, probe a running server **and** point to its source:

```bash
mcp-score http://localhost:3000/mcp --repo github:owner/repo
mcp-score stdio -- python my_server.py --repo github:owner/repo
```

## Output Formats

### Terminal (default)

Rich-formatted output with color-coded grades and scores:

```
╭──────────────────────────────────────────────────────────╮
│ MCP Server Score Report                                  │
│ mcp-servers/everything                                   │
╰──────────────────────────────────────────────────────────╯
  Overall Score:  78/100  Grade: B
  (Partial score — limited data available)

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━┓
┃ Category                             ┃     Score ┃   Wt. ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━┩
│ Schema Quality                       │         — │   25% │
│ Protocol Compliance                  │        86 │   20% │
│ Reliability                          │         — │   20% │
│ Docs & Maintenance                   │         — │   15% │
│ Security & Permissions               │        71 │   20% │
└──────────────────────────────────────┴───────────┴───────┘

  Flags:
    ⚠ NO_SOURCE — No repository URL or source code link found.

  Tools Found: 13
  Schema Valid: No
  Error Handling: 100/100
  Latency: 4ms
```

Use `--verbose` for additional detail:

```
  Probe Timing:
    Connect: 4ms
    Initialize: 546ms
    Ping: 1ms
    tools/list: 2ms

  Schema Issues:
    • get-resource-reference.resourceType: missing description

  Error Handling Details:
    unknown_tool: proper_error
    missing_required_params: proper_error
    wrong_param_type: proper_error
  Fuzz Score: 100/100
```

### JSON

Machine-readable output for pipelines and integrations:

```bash
mcp-score --format json stdio -- npx -y @modelcontextprotocol/server-everything stdio
```

```json
{
  "version": "0.1.0",
  "target": "stdio",
  "timestamp": "2026-03-07T22:55:57.129733+00:00",
  "score": {
    "composite": 78,
    "grade": "B",
    "type": "partial",
    "categories": {
      "schema_quality": null,
      "protocol": 86,
      "reliability": null,
      "docs_maintenance": null,
      "security": 71
    }
  },
  "flags": [
    {
      "key": "NO_SOURCE",
      "severity": "warning",
      "label": "No Source Code",
      "description": "No repository URL or source code link found."
    }
  ],
  "classification": {
    "category": "other",
    "targets": [],
    "publisher": "mcp-servers",
    "verified_publisher": false
  },
  "probe": {
    "is_reachable": true,
    "connection_ms": 3,
    "initialize_ms": 477,
    "ping_ms": 1,
    "tools_count": 13,
    "schema_valid": false,
    "schema_issues": [
      "get-resource-reference.resourceType: missing description"
    ],
    "error_handling_score": 100,
    "fuzz_score": 100
  },
  "reliability": {
    "uptime_pct": null,
    "latency_p50_ms": 3,
    "latency_p95_ms": null,
    "probe_count": 1
  }
}
```

### Markdown

Clean markdown for PR comments, docs, or saving to files:

```bash
mcp-score --format markdown stdio -- npx -y @modelcontextprotocol/server-everything stdio
```

Output:

> # MCP Server Score Report: mcp-servers/everything
>
> **Overall Score: 78/100 (Grade: B)**
> *Partial score — limited data available*
>
> | Category | Score | Weight |
> |---|---:|---:|
> | Schema Quality | — | 25% |
> | Protocol Compliance | 86 | 20% |
> | Reliability | — | 20% |
> | Docs & Maintenance | — | 15% |
> | Security & Permissions | 71 | 20% |
>
> ## Flags
>
> - **NO_SOURCE**: No repository URL or source code link found.
>
> ## Probe Results
>
> - **Tools Found**: 13
> - **Schema Valid**: No
> - **Error Handling**: 100/100
> - **Fuzz Resilience**: 100/100
> - **Latency**: 3ms

## Saving Reports

Use `-o` / `--output` to save a markdown report to a file. This works alongside any `--format` — you can view JSON in the terminal while saving markdown for records:

```bash
# Save report while viewing terminal output
mcp-score -o report.md stdio -- python my_server.py

# Save report while viewing JSON output
mcp-score --format json -o report.md http://localhost:3000/mcp
```

## CI/CD Integration

Use `--fail-below` to fail CI pipelines when a server doesn't meet a quality threshold:

```bash
# Fail if score is below B
mcp-score --fail-below B stdio -- python my_server.py

# JSON output for CI parsing + fail threshold + save report
mcp-score --format json --fail-below C -o score-report.md http://localhost:3000/mcp
```

Exit codes:
- `0` — Score meets or exceeds the threshold (or no threshold set)
- `1` — Score is below the threshold
- `2` — Error (connection failed, invalid input, rate limit, etc.)

### GitHub Actions Example

```yaml
- name: Score MCP Server
  run: |
    pip install mcp-score
    mcp-score --fail-below B -o score-report.md stdio -- python my_server.py
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

- name: Upload Score Report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: mcp-score-report
    path: score-report.md
```

## Scoring Methodology

`mcp-score` uses the same [mcp-scoring-engine](https://pypi.org/project/mcp-scoring-engine/) that powers the [MCP Scoreboard](https://mcpscoreboard.com). The full scoreboard methodology is documented at [mcpscoreboard.com/scoreboard/methodology](https://mcpscoreboard.com/scoreboard/methodology/). The CLI runs a **subset** of that pipeline — here's exactly what you get and what's different.

### What the CLI covers

The CLI can run up to **two data tiers** in a single invocation:

| Tier | Trigger | What Runs |
|---|---|---|
| **Deep Protocol Probe** | `http://...` or `stdio --` target | Connection, initialize, ping, tools/list, schema validation, error handling, fuzz testing |
| **Static Analysis** | `github:` target or `--repo` flag | 7 sub-metrics via GitHub API (schema completeness, description quality, docs coverage, maintenance pulse, dependency health, license clarity, version hygiene) |

Combine both for the most complete CLI score:

```bash
mcp-score http://localhost:3000/mcp --repo github:owner/repo
```

### What the Scoreboard adds

The [MCP Scoreboard](https://mcpscoreboard.com) runs a **continuous, multi-tier pipeline** on 23,000+ servers that goes well beyond what a single CLI run can do:

| Capability | CLI | Scoreboard |
|---|---|---|
| Deep protocol probe (schema, errors, fuzz) | Single run | Daily, with history |
| Static analysis (7 GitHub metrics) | Single run | Hourly, with freshness tracking |
| **Reliability monitoring** (uptime, p50/p95 latency) | Snapshot from 1 probe | 7-day rolling window from probes every 5 minutes |
| **Behavioral security analysis** (LLM source scan) | Not available | 3-pass LLM analysis of source code for prompt injection, exfiltration, hardcoded credentials |
| **Agent usability evaluation** | Not available | Multi-model LLM consensus (3 judges score clarity, completeness, confidence per tool) |
| **Sandbox probes** (local-only servers) | Not available | Docker-based install + probe for servers without remote endpoints |
| **Source code inference** (protocol score fallback) | Not available | LLM-inferred error handling and fuzz resilience from source when no live probe |
| **Schema drift detection** | Not available | Flags when source-defined tools differ from runtime tools |
| **Stale data decay** | Not applicable | Scores decay from full value at 7 days to 40% floor at 90+ days |
| **Score history & trends** | Not available | Daily snapshots, regression alerts |
| **8-source ingestion** | Not applicable | Registry, Awesome, Glama, PulseMCP, GitHub Topics, Smithery, best-of, Docker Hub |
| Red flag detection | Basic (from available data) | Full (includes behavioral, schema drift, stale analysis flags) |

### How this affects your score

A CLI-only score will typically be **partial** — meaning fewer categories are populated and the composite is computed from whatever data is available. Here's what each target type produces:

| Target | Categories scored | Score type |
|---|---|---|
| `stdio -- ...` or `http://...` only | Protocol Compliance, Security | Partial |
| `github:...` only | Schema Quality, Docs & Maintenance, Security | Partial |
| Probe + `--repo` combined | Schema Quality, Protocol Compliance, Docs & Maintenance, Security | Full |

**Reliability** always shows as `—` in CLI output because it requires accumulated probe history (the scoreboard probes every 5 minutes over 7 days). **Agent Usability** is only available on the scoreboard (requires multi-model LLM evaluation).

### Scoring categories

Scores are computed across five weighted categories (six with agent usability on the scoreboard):

| Category | Weight | What It Measures | CLI Source |
|---|---:|---|---|
| Schema Quality | 25% | Tool input schemas, descriptions, completeness | Static analysis (`--repo` / `github:`) |
| Protocol Compliance | 20% | MCP protocol correctness, error handling, fuzz resilience | Deep probe (`http://` / `stdio`) |
| Reliability | 20% | Uptime percentage, p50/p95 latency | Single-probe latency snapshot (no uptime) |
| Docs & Maintenance | 15% | README, recent commits, dependency health, license, versioning | Static analysis (`--repo` / `github:`) |
| Security & Permissions | 20% | Credential handling, transport security, distribution clarity | Registry metadata + basic analysis |
| Agent Usability | 15%* | Tool clarity, input completeness, agent confidence | *Scoreboard only* |

\* Enhanced weights (with Agent Usability) are only applied on the scoreboard. The CLI always uses standard 5-category weights.

### Grade thresholds

| Grade | Score Range |
|---|---|
| A+ | 95–100 |
| A | 85–94 |
| B | 70–84 |
| C | 55–69 |
| D | 40–54 |
| F | 0–39 |

### Flags

The scorer detects quality and security red flags. Critical flags impose hard caps on the composite score:

| Flag | Severity | Cap | Description |
|---|---|---|---|
| `DEAD_REPO` | Critical | 0 | Repository is deleted or inaccessible |
| `EXFILTRATION_RISK` | Critical | 25 | Tools may exfiltrate data |
| `PROMPT_INJECTION` | Critical | 30 | Tool descriptions contain prompt injection patterns |
| `REPO_ARCHIVED` | Critical | 40 | Repository is archived |
| `STAGING_ARTIFACT` | Warning | 55 | Appears to be a test/staging server |
| `NO_SOURCE` | Warning | — | No repository URL or source code link found |
| `STALE_PROJECT` | Warning | — | No commits in over 12 months |

## What gets probed

### Deep protocol probe (HTTP / stdio)

When you score a running server, `mcp-score` runs these checks:

1. **Connection** — TCP/stdio connection establishment, latency measurement
2. **Initialize** — MCP handshake, protocol version negotiation, server name and version extraction
3. **Ping** — `ping` request/response round-trip
4. **tools/list** — Enumerate all tools, measure response time
5. **Schema Validation** — Validate every tool's `inputSchema` against JSON Schema spec
6. **Error Handling** — Send malformed requests (unknown tool, missing params, wrong types) and verify proper error responses
7. **Fuzz Testing** — Send edge-case inputs (empty strings, huge numbers, nested objects) to test resilience

### Static analysis (GitHub)

When you provide a `--repo` or use `github:` target:

1. **Schema Completeness** — Are tool schemas fully specified with types and descriptions?
2. **Description Quality** — Are tool and parameter descriptions helpful for AI agents?
3. **Documentation Coverage** — Does the repo have a README, examples, API docs?
4. **Maintenance Pulse** — Recent commits, active development, issue responsiveness
5. **Dependency Health** — Are dependencies up to date? Known vulnerabilities?
6. **License Clarity** — Is there a clear, permissive license?
7. **Version Hygiene** — Semantic versioning, tagged releases, changelog

### What the CLI doesn't run

For the complete picture — including behavioral security scanning, agent usability evaluation, reliability monitoring, and score trends — submit your server to the [MCP Scoreboard](https://mcpscoreboard.com). It's free for public servers.

## Development

```bash
git clone https://github.com/Brightwing-Systems-LLC/mcp-score.git
cd mcp-score
pip install -e ".[dev]"
python3 -m pytest tests/ -v
```

83 tests covering CLI argument parsing, runner orchestration, and all three output formatters.

## Related Projects

- [mcp-scoring-engine](https://github.com/Brightwing-Systems-LLC/mcp-scoring-engine) — The scoring engine library (used by this CLI and the MCP Scoreboard)
- [MCP Scoreboard](https://mcpscoreboard.com) — Public leaderboard scoring 23,000+ MCP servers
- [PatchworkMCP](https://patchworkmcp.com) — Continuous monitoring, agent feedback, and improvement guides

## License

MIT — Brightwing Systems LLC
