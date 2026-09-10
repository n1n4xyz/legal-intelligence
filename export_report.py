#!/usr/bin/env python3
"""
Export an /analyze API response to final_report.md
===================================================
Usage:
    python export_report.py report.json [test_output.txt] [final_report.md]

report.json      JSON returned by POST /analyze
test_output.txt  optional, output of `python tests/test_todos.py`
final_report.md  optional output path (default: final_report.md)
"""

import json
import sys
from pathlib import Path


def build_markdown(report: dict, test_output: str = "") -> str:
    scenario = report.get("scenario", {})
    meta = report.get("metadata", {})
    sections = report.get("sections", [])

    lines = [
        f"# Legal Intelligence Report: {scenario.get('case_name', 'Unknown case')}",
        "",
        f"Generated {report.get('timestamp', '')} with `{meta.get('model', 'unknown model')}`.",
        "",
        "## Run summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Case type | {scenario.get('case_type', '')} |",
        f"| Urgency | {scenario.get('urgency_level', '')} |",
        f"| Sections | {len(sections)} |",
        f"| Confidence score | {report.get('confidence_score', 0):.3f} |",
        f"| Total tokens | {report.get('total_tokens', 0):,} |",
        f"| Total cost (USD) | ${report.get('total_cost', 0):.4f} |",
        f"| Processing time | {report.get('processing_time', 0):.1f} s |",
        f"| Quality threshold | {meta.get('quality_threshold', '')} |",
        f"| Quality retries used | {meta.get('quality_retries_used', 0)} |",
        f"| Sections below threshold | {', '.join(meta.get('sections_below_threshold', [])) or 'none'} |",
        f"| Failed sections | {len(meta.get('failed_sections', []))} |",
        "",
        "## Context chain and quality audit",
        "",
        f"Sequence: {' -> '.join(meta.get('section_sequence', []))}. "
        f"Each section received all previously completed sections as context.",
        "",
        "| # | Section | Agent | Attempt scores | Final score | Tokens | Cost (USD) |",
        "|---|---|---|---|---|---|---|",
    ]

    audit = {a["section"]: a for a in meta.get("quality_audit", [])}
    for i, s in enumerate(sections, 1):
        a = audit.get(s["type"], {})
        attempts = ", ".join(f"{x:.2f}" for x in a.get("attempt_scores", [])) or "n/a"
        lines.append(
            f"| {i} | {s['title']} | {s['agent_type']} | {attempts} | "
            f"{s['quality_score']:.2f} | {s['tokens_used']:,} | ${s['cost']:.4f} |"
        )

    lines += ["", "## Executive summary", "", "```", report.get("executive_summary", "").strip(), "```", ""]

    for i, s in enumerate(sections, 1):
        lines += [
            f"## {i}. {s['title']}",
            "",
            f"*Agent: {s['agent_type']} | quality score {s['quality_score']:.2f}*",
            "",
            s["content"].strip(),
            "",
        ]

    if test_output.strip():
        lines += ["## Test output", "", "```", test_output.strip(), "```", ""]

    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    report = json.loads(Path(sys.argv[1]).read_text())
    if "sections" not in report:
        print(f"{sys.argv[1]} is not an /analyze report. API said: {report}")
        return 1

    test_output = Path(sys.argv[2]).read_text() if len(sys.argv) > 2 and Path(sys.argv[2]).exists() else ""
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("final_report.md")

    out_path.write_text(build_markdown(report, test_output))
    print(f"Wrote {out_path} ({len(report['sections'])} sections, ${report.get('total_cost', 0):.4f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
