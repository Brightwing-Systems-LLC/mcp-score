"""JSON output formatter for score results."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from mcp_scoring_engine import ScoreResult

from mcp_score import __version__


def format_json(result: ScoreResult, *, target: str = "") -> str:
    """Serialize a ScoreResult to JSON."""
    categories = {
        "schema_quality": result.schema_quality_score,
        "protocol": result.protocol_score,
        "reliability": result.reliability_score,
        "docs_maintenance": result.docs_maintenance_score,
        "security": result.security_score,
    }
    if result.agent_usability_score is not None:
        categories["agent_usability"] = result.agent_usability_score

    from .cta import get_random_cta

    hook, url, label = get_random_cta()

    output = {
        "version": __version__,
        "target": target,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "score": {
            "composite": result.composite_score,
            "grade": result.grade,
            "type": result.score_type,
            "categories": categories,
        },
        "flags": [
            {
                "key": f.key,
                "severity": f.severity,
                "label": f.label,
                "description": f.description,
            }
            for f in result.flags
        ],
        "classification": {
            "category": result.category,
            "targets": result.targets,
            "publisher": result.publisher,
            "verified_publisher": result.verified_publisher,
        },
        "cta": {
            "message": hook,
            "url": url,
            "label": label,
        },
    }

    # Add probe data if available
    if result.deep_probe:
        probe = result.deep_probe
        output["probe"] = {
            "is_reachable": probe.is_reachable,
            "connection_ms": probe.connection_ms,
            "initialize_ms": probe.initialize_ms,
            "ping_ms": probe.ping_ms,
            "tools_count": probe.tools_count,
            "schema_valid": probe.schema_valid,
            "schema_issues": probe.schema_issues,
            "error_handling_score": probe.error_handling_score,
            "fuzz_score": probe.fuzz_score,
        }
        if probe.error_message:
            output["probe"]["error_message"] = probe.error_message

    # Add static analysis if available
    if result.static_analysis:
        sa = result.static_analysis
        output["static_analysis"] = {
            "schema_completeness": sa.schema_completeness,
            "description_quality": sa.description_quality,
            "documentation_coverage": sa.documentation_coverage,
            "maintenance_pulse": sa.maintenance_pulse,
            "dependency_health": sa.dependency_health,
            "license_clarity": sa.license_clarity,
            "version_hygiene": sa.version_hygiene,
            "stars": sa.stars_count,
            "open_issues": sa.open_issues_count,
            "latest_version": sa.latest_version,
        }

    # Add reliability if available
    if result.reliability_data:
        rel = result.reliability_data
        output["reliability"] = {
            "uptime_pct": rel.uptime_pct,
            "latency_p50_ms": rel.latency_p50_ms,
            "latency_p95_ms": rel.latency_p95_ms,
            "probe_count": rel.probe_count,
        }

    return json.dumps(output, indent=2)
