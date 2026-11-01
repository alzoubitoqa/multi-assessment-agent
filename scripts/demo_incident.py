"""Offline demonstration of the staged, audited incident workflow.

Usage: python -m scripts.demo_incident --scenario integrity_false_positive
"""

import argparse
import json
import tempfile
from pathlib import Path

from app.governance.simulator import (
    get_run_history, get_scenario, record_human_decision, release_next_event, start_scenario,
)
from app.policy.kb import search_policies


def _offline_lookup(query, jurisdiction="UAE", limit=3):
    return search_policies(query, jurisdiction=jurisdiction, limit=limit, use_vector=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["integrity_false_positive", "assessment_error"],
                        default="integrity_false_positive")
    parser.add_argument("--output", help="Optional JSON audit output path")
    parser.add_argument("--record-demo-review", action="store_true",
                        help="Append an explicitly synthetic human review record after the last event")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "incident_demo.sqlite"
        run_id = start_scenario(args.scenario, database)
        scenario = get_scenario(args.scenario)
        print(f"Scenario: {scenario['title']}")
        for _ in scenario["events"]:
            step = release_next_event(run_id, database, _offline_lookup)
            print(f"\nEvent {step['event_number']}: {step['event']['title']}")
            for item in step["assessments"]:
                print(f"  {item['role_label']}: {item['recommendation']}")
                print("    References:", ", ".join(c["id"] for c in item["citations"]))
        if args.record_demo_review:
            record_human_decision(run_id, "Synthetic demonstration reviewer",
                                  "escalate_review",
                                  "Sample decision for testing the audit interface; not an actual institutional approval.",
                                  database)
        history = get_run_history(run_id, database)
        if args.output:
            Path(args.output).write_text(json.dumps(history, indent=2), encoding="utf-8")
            print("Audit saved to:", args.output)
        print("\nFinal status:", history["human_decision"])


if __name__ == "__main__":
    main()
