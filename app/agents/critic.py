import os
from typing import Any, Dict, List, Optional
from ..llm.nightshift_client import NightshiftClient
from ..memory.hmem_engine import HMemEngine, HMemRecord


class SkepticalCritic:
    """SkepticalCritic Agent.
    
    Adversarial statistical auditor powered by NVIDIA Nemotron-3 Super 120B.
    Evaluates evidence against strict quantitative thresholds. If confidence < 0.70,
    emits CLAIM_BLOCKED and triggers BRANCH_RETRY, updating H-MEM lineage.
    """

    def __init__(self, client: Optional[NightshiftClient] = None) -> None:
        self.client = client or NightshiftClient()
        self.model_name = self.client.model_name

    def critique(
        self,
        hypothesis_id: str,
        hypothesis_text: str,
        query: str,
        evidence_rows: List[Dict[str, Any]],
        turn_id: int,
        hmem: HMemEngine,
        scenario_verdict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Audits causal link between retrieved data and observed profit margin drop."""
        eval_result = self.client.evaluate_hypothesis(
            hypothesis_id=hypothesis_id,
            hypothesis_text=hypothesis_text,
            query=query,
            evidence_rows=evidence_rows,
            scenario_verdict=scenario_verdict
        )

        confidence_score = float(eval_result.get("confidence_score", 0.5))
        reasoning = eval_result.get("reasoning", "Statistical sufficiency evaluation completed.")

        if confidence_score < 0.70:
            event = "CLAIM_BLOCKED"
            status = "BRANCH_RETRY"
            new_branch_id = f"{hypothesis_id}_BRANCH_COMBINED" if hypothesis_id == "H1" else "H_DEEP_DIVE"
            
            # Record rejection in H-MEM and append to trust ledger
            hmem.reject_and_branch(
                rejected_id=hypothesis_id,
                new_id=new_branch_id,
                reason=reasoning,
                critic_confidence=confidence_score
            )
        else:
            event = "APPROVED_CLAIM"
            status = "VERIFIED"
            
            # Register verified claim in working tier
            claim_rec = HMemRecord(
                id=hypothesis_id,
                tier="working",
                content=hypothesis_text,
                source="SkepticalCritic",
                confidence=confidence_score,
                provenance={
                    "turn_id": turn_id,
                    "evidence_row_count": len(evidence_rows),
                    "model": self.model_name,
                    "reasoning": reasoning
                },
                entities=[hypothesis_id, "VerifiedClaim"]
            )
            hmem.mine(claim_rec)

        return {
            "turn_id": turn_id,
            "agent": "SkepticalCritic",
            "model": self.model_name,
            "event": event,
            "hypothesis_id": hypothesis_id,
            "confidence_score": confidence_score,
            "reasoning": reasoning,
            "status": status
        }
