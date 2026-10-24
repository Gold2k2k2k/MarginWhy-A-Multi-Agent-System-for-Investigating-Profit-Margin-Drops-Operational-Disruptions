from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class HMemRecord:
    """Standard Meterless H-MEM record with full provenance and lineage tracking."""
    id: str
    tier: str  # "short_term" | "working" | "long_term"
    content: str
    source: str
    confidence: float
    provenance: Dict[str, Any]
    entities: List[str] = field(default_factory=list)
    relationships: List[Dict[str, str]] = field(default_factory=list)
    replacement_lineage: Optional[Dict[str, str]] = None
    status: str = "ACTIVE"  # "ACTIVE" | "REJECTED" | "CONSOLIDATED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HMemEngine:
    """Meterless H-MEM (Hierarchical Memory) Living Knowledge Graph.
    
    Implements 3-tier memory stratification, immutable trust ledger audit trail,
    adversarial claim rejection branching with lineage tracking, and Markovian
    bounded carryover to enforce efficient token usage across investigation turns.
    """

    def __init__(self) -> None:
        self.records: Dict[str, HMemRecord] = {}
        self.trust_ledger: List[Dict[str, Any]] = []

    def mine(self, record: HMemRecord) -> HMemRecord:
        """Stores a new record across tiers and appends an immutable audit event."""
        self.records[record.id] = record
        self._audit(
            action="MINE",
            record_id=record.id,
            details={
                "tier": record.tier,
                "confidence": record.confidence,
                "status": record.status,
                "source": record.source
            }
        )
        return record

    def reject_and_branch(
        self,
        rejected_id: str,
        new_id: str,
        reason: str,
        critic_confidence: float
    ) -> None:
        """Marks a hypothesis as REJECTED and records replacement lineage in trust ledger."""
        if rejected_id in self.records:
            rec = self.records[rejected_id]
            rec.status = "REJECTED"
            rec.confidence = critic_confidence
            rec.replacement_lineage = {
                "superseded_id": rejected_id,
                "replaced_by": new_id,
                "reason": reason
            }
            self._audit(
                action="CLAIM_BLOCKED_LINEAGE",
                record_id=rejected_id,
                details=rec.replacement_lineage
            )

    def retrieve_hybrid(
        self,
        query_entities: List[str],
        min_confidence: float = 0.0,
        include_rejected: bool = False
    ) -> List[HMemRecord]:
        """Weighted hybrid retrieval over confidence, entity overlap, and tier priority."""
        scored_records: List[Tuple[float, HMemRecord]] = []
        for rec in self.records.values():
            if not include_rejected and rec.status == "REJECTED":
                continue
            if rec.confidence < min_confidence:
                continue

            entity_overlap = len(set(query_entities).intersection(set(rec.entities)))
            tier_weight = 1.2 if rec.tier == "working" else (1.1 if rec.tier == "long_term" else 1.0)
            score = (rec.confidence * 0.6) + (entity_overlap * 0.3) * tier_weight
            scored_records.append((score, rec))

        scored_records.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored_records]

    def get_rejected_hypotheses(self) -> List[str]:
        """Returns IDs of all previously refuted hypotheses."""
        return [r.id for r in self.records.values() if r.status == "REJECTED"]

    def build_markovian_carryover(self) -> Dict[str, Any]:
        """Produces a bounded state summary so agents never reload bloated raw transcripts."""
        return {
            "rejected_hypotheses": [
                {
                    "id": r.id,
                    "reason": (r.replacement_lineage or {}).get("reason", ""),
                    "confidence": r.confidence
                }
                for r in self.records.values()
                if r.status == "REJECTED"
            ],
            "approved_claims": [
                {
                    "id": r.id,
                    "content": r.content,
                    "confidence": r.confidence,
                    "provenance": r.provenance
                }
                for r in self.records.values()
                if r.status in ("ACTIVE", "CONSOLIDATED") and r.confidence >= 0.70
            ],
            "active_hypotheses": [
                {
                    "id": r.id,
                    "content": r.content,
                    "confidence": r.confidence
                }
                for r in self.records.values()
                if r.tier == "working" and r.status == "ACTIVE"
            ],
            "total_records": len(self.records),
            "ledger_mutations": len(self.trust_ledger)
        }

    def consolidate_sleep_cycle(self) -> int:
        """Promotes verified working memories (confidence >= 0.70) into the long_term tier."""
        promoted = 0
        for rec in self.records.values():
            if rec.tier == "working" and rec.status == "ACTIVE" and rec.confidence >= 0.70:
                rec.tier = "long_term"
                rec.status = "CONSOLIDATED"
                promoted += 1
                self._audit("CONSOLIDATE", rec.id, {"new_tier": "long_term", "confidence": rec.confidence})
        return promoted

    def _audit(self, action: str, record_id: str, details: Dict[str, Any]) -> None:
        """Appends an immutable event to the audit ledger."""
        self.trust_ledger.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "record_id": record_id,
            "details": details
        })
