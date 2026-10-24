#!/usr/bin/env python3
"""MarginWhy: Unified CLI Entry Point for Root-Cause Margin Anomaly Investigation.

Usage Examples:
    # 1. Run direct query in offline sample mode:
    python run.py --query "Why did net profit margin for Electronics drop 18.5% in Q3?" --sample-mode

    # 2. Run from packaged scenario bundle:
    python run.py --input data/samples/scenario_1_electronics_q3.json --sample-mode

    # 3. Run scenario 2 (Apparel returns):
    python run.py --query "Why did Fall-Winter apparel net revenue decline by 14.2% across catalog channels?" --sample-mode
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.agents.orchestrator import MarginWhyOrchestrator


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MarginWhy: Multi-Agent Root-Cause Investigation for Retail Profit Drops"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Why did net profit margin for Electronics drop 18.5% in Q3?",
        help="Natural language business question regarding margin anomaly."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to an input scenario JSON file in data/samples/."
    )
    parser.add_argument(
        "--sample-mode",
        action="store_true",
        default=True,
        help="Run in offline deterministic sample mode (default: True)."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    # Determine query and scenario file
    query = args.query
    scenario_file = "scenario_1_electronics_q3.json"

    if args.input:
        input_path = Path(args.input)
        if input_path.exists():
            scenario_file = input_path.name
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    bundle = json.load(f)
                    query = bundle.get("query", query)
            except Exception as e:
                print(f"[Warning] Could not parse input bundle query: {e}")
        else:
            print(f"[Error] Provided input file '{args.input}' does not exist.")
            sys.exit(1)
    else:
        # Match scenario file based on query keywords
        q_lower = query.lower()
        if "apparel" in q_lower:
            scenario_file = "scenario_2_apparel_returns.json"
        elif "shipping" in q_lower or "freight" in q_lower or "logistics" in q_lower:
            scenario_file = "scenario_3_shipping_delay.json"
        else:
            scenario_file = "scenario_1_electronics_q3.json"

    # Set environment variable for sample mode
    if args.sample_mode:
        os.environ["SAMPLE_MODE"] = "true"

    orchestrator = MarginWhyOrchestrator(sample_mode=args.sample_mode)
    result = orchestrator.run_investigation(query=query, scenario_file=scenario_file)

    print("=" * 80)
    print("FINAL INVESTIGATION REPORT (Markdown):")
    print("=" * 80)
    print(result["report_markdown"])
    print("=" * 80)
    print(f"Investigation complete. Trace saved to logs/trace.jsonl")


if __name__ == "__main__":
    main()
