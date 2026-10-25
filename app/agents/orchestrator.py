import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..adapters.zetaris_adapter import ZetarisAdapter
from ..llm.nightshift_client import NightshiftClient
from ..memory.hmem_engine import HMemEngine
from .planner import HypothesisPlanner
from .retriever import ZetarisRetriever
from .critic import SkepticalCritic
from .synthesizer import ActionReportWriter

_TRACE_LOCK = threading.Lock()


class MarginWhyOrchestrator:
    """Non-linear Adversarial Multi-Agent Loop Controller for MarginWhy.
    
    Coordinates the 4 specialized agents across an iterative critic loop:
    HypothesisPlanner -> ZetarisRetriever -> SkepticalCritic -> ActionReportWriter.
    Enforces Meterless H-MEM Markovian carryover, max turn boundaries,
    and structured JSONL trace logging to logs/trace.jsonl.
    """

    MAX_TURNS: int = 3

    def __init__(
        self,
        trace_log_path: Optional[str] = None,
        sample_mode: bool = True
    ) -> None:
        self.sample_mode = sample_mode
        self.adapter = ZetarisAdapter()
        self.hmem = HMemEngine()
        self.nightshift = NightshiftClient()

        self.planner = HypothesisPlanner()
        self.retriever = ZetarisRetriever(adapter=self.adapter)
        self.critic = SkepticalCritic(client=self.nightshift)
        self.synthesizer = ActionReportWriter()

        # Setup trace log file path
        if trace_log_path:
            self.trace_file = Path(trace_log_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.trace_file = base_dir / "logs" / "trace.jsonl"
            
        self.trace_file.parent.mkdir(parents=True, exist_ok=True)
        self.trace_events: List[Dict[str, Any]] = []

    def _log_event(self, event_data: Dict[str, Any]) -> None:
        """Appends a structured trace event to memory, stdout, and logs/trace.jsonl."""
        event_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event_data
        }
        line = json.dumps(event_record, ensure_ascii=False) + "\n"

        with _TRACE_LOCK:
            self.trace_events.append(event_record)

            # Append to JSONL file
            with open(self.trace_file, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()

            # Pretty print to stdout for interactive viewing
            agent_name = event_record.get("agent", "System")
            event_name = event_record.get("event", "INFO")
            status = event_record.get("status", "")
            print(f"[{event_record['timestamp']}] [{agent_name}] {event_name} ({status})")
            if "sql_query" in event_record:
                print(f"   SQL: {event_record['sql_query']}")
            if "reasoning" in event_record:
                print(f"   Reasoning: {event_record['reasoning']}")
            if "confidence_score" in event_record:
                print(f"   Confidence Score: {event_record['confidence_score']}")
            print()

    def run_investigation(
        self,
        query: str,
        scenario_file: str = "scenario_1_electronics_q3.json"
    ) -> Dict[str, Any]:
        """Runs the adversarial multi-agent investigation loop."""
        print("=" * 80)
        print(f"MarginWhy Multi-Agent Investigation Initiated")
        print(f"Query: {query}")
        print(f"Dataset Scenario: {scenario_file} | Sample Mode: {self.sample_mode}")
        print("=" * 80 + "\n")

        approved_claims: List[Dict[str, Any]] = []
        turn = 0

        while turn < self.MAX_TURNS:
            turn += 1
            print(f"--- [Turn {turn} / {self.MAX_TURNS}] ---")

            # Step 1: HypothesisPlanner plans the investigation turn
            plan = self.planner.plan_turn(
                query=query,
                turn_id=turn,
                hmem=self.hmem,
                scenario_file=scenario_file
            )
            self._log_event(plan)

            # Step 2: ZetarisRetriever fetches SQL evidence from Zetaris / local sample
            retrieval = self.retriever.retrieve_evidence(
                hypothesis_id=plan["hypothesis_id"],
                sql=plan["sql"],
                turn_id=turn,
                hmem=self.hmem,
                scenario_file=scenario_file
            )
            self._log_event({
                "turn_id": turn,
                "agent": retrieval["agent"],
                "model": retrieval["model"],
                "event": retrieval["event"],
                "hypothesis_id": retrieval["hypothesis_id"],
                "sql_query": retrieval["sql_query"],
                "data_source": retrieval["data_source"],
                "row_count": retrieval["row_count"],
                "status": retrieval["status"]
            })

            # Step 3: SkepticalCritic audits the evidence
            critique = self.critic.critique(
                hypothesis_id=plan["hypothesis_id"],
                hypothesis_text=plan["hypothesis_text"],
                query=query,
                evidence_rows=retrieval["rows"],
                turn_id=turn,
                hmem=self.hmem,
                scenario_verdict=retrieval.get("scenario_verdict")
            )
            self._log_event(critique)

            if critique["event"] == "APPROVED_CLAIM":
                approved_claims.append(critique)
                print(f">>> [Critic Loop SUCCESS] Approved Hypothesis: {plan['hypothesis_id']} with Confidence {critique['confidence_score']}\n")
                break
            else:
                print(f">>> [Critic Loop REJECT] Hypothesis {plan['hypothesis_id']} BLOCKED. Forcing orthogonal branch...\n")

        # Step 4: Promote verified memories to long_term tier
        promoted_count = self.hmem.consolidate_sleep_cycle()
        print(f"H-MEM Consolidation: {promoted_count} verified record(s) promoted to long_term tier.")

        # Step 5: ActionReportWriter synthesizes verified evidence
        report_data = self.synthesizer.generate_report(
            query=query,
            approved_claims=approved_claims,
            hmem=self.hmem,
            turn_count=turn
        )
        self._log_event({
            "turn_id": turn,
            "agent": report_data["agent"],
            "model": report_data["model"],
            "event": report_data["event"],
            "primary_hypothesis": report_data["primary_hypothesis"],
            "confidence_score": report_data["confidence_score"],
            "status": report_data["status"]
        })

        return {
            "query": query,
            "scenario_file": scenario_file,
            "turns_executed": turn,
            "approved_claims": approved_claims,
            "report_markdown": report_data["report_markdown"],
            "hmem_state": self.hmem.build_markovian_carryover(),
            "trust_ledger": self.hmem.trust_ledger,
            "trace_events": self.trace_events
        }
