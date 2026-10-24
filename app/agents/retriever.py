import os
import uuid
from typing import Any, Dict, List, Optional
from ..adapters.zetaris_adapter import ZetarisAdapter
from ..memory.hmem_engine import HMemEngine, HMemRecord


class ZetarisRetriever:
    """ZetarisRetriever Agent.
    
    Translates planned hypotheses into dialect-compliant Zetaris Lightning SQL,
    enforcing mandatory LIMIT, 30-second timeouts, two-attempt auto-retry on
    transient errors, and seamless fallback to bundled scenario datasets.
    Stores query telemetry in H-MEM short_term episodic tier.
    """

    def __init__(self, adapter: Optional[ZetarisAdapter] = None) -> None:
        self.adapter = adapter or ZetarisAdapter()
        self.model_name = "zetaris-lightning-sql-adapter"

    def retrieve_evidence(
        self,
        hypothesis_id: str,
        sql: str,
        turn_id: int,
        hmem: HMemEngine,
        scenario_file: str = "scenario_1_electronics_q3.json"
    ) -> Dict[str, Any]:
        """Executes Lightning SQL query against Zetaris AI Data Harness."""
        exec_result = self.adapter.execute_sql(
            sql=sql,
            hypothesis_id=hypothesis_id,
            scenario_file=scenario_file
        )

        rows = exec_result.get("rows", [])
        clean_sql = exec_result.get("sql", sql)
        data_source = exec_result.get("source", "Zetaris_TPCDS_DB")

        # Save query execution in H-MEM short_term tier (episodic memory)
        record_id = f"query_{turn_id}_{hypothesis_id}_{uuid.uuid4().hex[:6]}"
        hmem_rec = HMemRecord(
            id=record_id,
            tier="short_term",
            content=f"Executed query for {hypothesis_id}: {clean_sql} returned {len(rows)} records",
            source=data_source,
            confidence=1.0,
            provenance={
                "turn_id": turn_id,
                "hypothesis_id": hypothesis_id,
                "sql_query": clean_sql,
                "rows_retrieved": len(rows),
                "adapter_status": exec_result.get("status")
            },
            entities=[hypothesis_id]
        )
        hmem.mine(hmem_rec)

        return {
            "turn_id": turn_id,
            "agent": "ZetarisRetriever",
            "model": self.model_name,
            "event": "ZETARIS_QUERY_EXECUTED",
            "hypothesis_id": hypothesis_id,
            "sql_query": clean_sql,
            "data_source": data_source,
            "rows": rows,
            "row_count": len(rows),
            "scenario_verdict": exec_result.get("critic_verdict"),
            "status": "SUCCESS"
        }
