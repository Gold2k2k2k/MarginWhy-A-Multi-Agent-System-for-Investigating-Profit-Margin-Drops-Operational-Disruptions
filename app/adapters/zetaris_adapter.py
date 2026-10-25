import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error


class ZetarisAdapter:
    """Zetaris AI Data Harness & Lightning SQL Adapter.
    
    Provides high-reliability query execution over Zetaris Lightning SQL
    (supporting TPCDS_DB and NY_TAXI), automatic string-to-numeric type coercion,
    strict 30-second timeouts, two-tier retry logic, and seamless zero-dependency
    sample dataset fallback for offline evaluation.
    """

    def __init__(self) -> None:
        self.rest_url = os.getenv("ZETARIS_REST_URL", "http://localhost:8888/api/v1.0").rstrip("/")
        self.base_url = os.getenv("ZETARIS_BASE_URL", "http://localhost:3000").rstrip("/")
        self.org_id = os.getenv("ZETARIS_ORG_ID", "1")
        self.api_key = os.getenv("ZETARIS_API_KEY", "")
        self.query_limit = int(os.getenv("ZETARIS_QUERY_LIMIT", "1000"))
        self.timeout_sec = int(os.getenv("ZETARIS_TIMEOUT_SEC", "30"))
        self.sample_mode = os.getenv("SAMPLE_MODE", "true").lower() == "true"

    @staticmethod
    def _coerce_numeric_row(row: Dict[str, Any]) -> Dict[str, Any]:
        """Zetaris REST returns numeric/decimal values as strings (including exponent notation).
        
        Coerces strings that represent integers or floats into their native numeric types.
        """
        coerced: Dict[str, Any] = {}
        for k, v in row.items():
            if isinstance(v, str):
                v_strip = v.strip()
                try:
                    coerced[k] = int(v_strip)
                    continue
                except ValueError:
                    pass
                try:
                    coerced[k] = float(v_strip)
                    continue
                except ValueError:
                    pass
            coerced[k] = v
        return coerced

    def _resolve_sample_path(self, scenario_file: str) -> Path:
        """Resolves sample path whether executed from repo root or subdirectories."""
        base_dir = Path(__file__).resolve().parent.parent.parent
        samples_dir = (base_dir / "data" / "samples").resolve()
        target_path = (samples_dir / scenario_file).resolve()
        try:
            target_path.relative_to(samples_dir)
        except ValueError:
            return samples_dir / "__invalid_traversal__"
        if target_path.exists():
            return target_path
        # Fallback to relative path if available
        rel_path = (Path("data") / "samples" / scenario_file).resolve()
        try:
            rel_path.relative_to(samples_dir)
            if rel_path.exists():
                return rel_path
        except ValueError:
            pass
        return target_path

    def execute_sql(
        self,
        sql: str,
        hypothesis_id: str,
        scenario_file: str = "scenario_1_electronics_q3.json"
    ) -> Dict[str, Any]:
        """Executes a single Lightning SQL query with mandatory LIMIT and timeout safety.
        
        Falls back to local sample scenario if SAMPLE_MODE=true or on network failure.
        """
        clean_sql = sql.strip().rstrip(";")
        if "LIMIT" not in clean_sql.upper() and clean_sql.upper().startswith("SELECT"):
            clean_sql = f"{clean_sql} LIMIT {self.query_limit}"

        # If sample mode is active or API key is not configured, load from benchmark sample bundle
        if self.sample_mode or not self.api_key:
            return self._load_sample_fallback(
                hypothesis_id, clean_sql, scenario_file, reason="SAMPLE_MODE_ACTIVE_OR_UNCONFIGURED_KEY"
            )

        # Live query attempt with 2-tier retry and 30s timeout
        for attempt in range(1, 3):
            req_id = str(uuid.uuid4())
            payload = json.dumps({
                "sql": clean_sql,
                "queryId": req_id,
                "limit": self.query_limit
            }).encode("utf-8")

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "X-Org-ID": str(self.org_id),
                "X-Request-ID": req_id
            }

            req = urllib.request.Request(
                f"{self.base_url}/api/proxy/query",
                data=payload,
                headers=headers,
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                    raw_data = json.loads(resp.read().decode("utf-8"))
                    raw_rows = raw_data.get("rows", [])
                    rows = [self._coerce_numeric_row(r) for r in raw_rows]
                    return {
                        "status": "SUCCESS",
                        "source": "ZETARIS_LIVE",
                        "request_id": req_id,
                        "sql": clean_sql,
                        "rows": rows,
                        "row_count": len(rows)
                    }
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                if attempt == 2:
                    return self._load_sample_fallback(
                        hypothesis_id, clean_sql, scenario_file, reason=f"UpstreamTimeout/ConnectionError: {exc}"
                    )
                time.sleep(1.0)

        return self._load_sample_fallback(hypothesis_id, clean_sql, scenario_file, reason="UNKNOWN_FALLBACK")

    def _load_sample_fallback(
        self,
        hypothesis_id: str,
        sql: str,
        scenario_file: str,
        reason: str
    ) -> Dict[str, Any]:
        """Loads and coerces rows from bundled scenario JSON files."""
        sample_path = self._resolve_sample_path(scenario_file)
        if not sample_path.exists():
            return {
                "status": "FALLBACK_EMPTY",
                "fallback_reason": f"Sample file not found at {sample_path}",
                "source": f"LOCAL_SAMPLE:{scenario_file}",
                "sql": sql,
                "rows": [],
                "row_count": 0
            }

        try:
            with open(sample_path, "r", encoding="utf-8") as f:
                bundle = json.load(f)
        except Exception as e:
            return {
                "status": "FALLBACK_EMPTY",
                "fallback_reason": f"Sample file could not be read or parsed as JSON: {e}",
                "source": f"LOCAL_SAMPLE:{scenario_file}",
                "sql": sql,
                "rows": [],
                "row_count": 0
            }

        queries_map = bundle.get("queries", {})
        
        # Match hypothesis by exact key or prefix match
        target_data = queries_map.get(hypothesis_id)
        if not target_data:
            for k, v in queries_map.items():
                if k in hypothesis_id or hypothesis_id in k:
                    target_data = v
                    break

        if not target_data and queries_map:
            # Fall back to first query in bundle
            target_data = next(iter(queries_map.values()))

        raw_rows = target_data.get("rows", []) if target_data else []
        coerced_rows = [self._coerce_numeric_row(r) for r in raw_rows]

        return {
            "status": "FALLBACK_SAMPLE",
            "fallback_reason": reason,
            "source": f"LOCAL_SAMPLE:{scenario_file}",
            "sql": target_data.get("sql", sql) if target_data else sql,
            "rows": coerced_rows,
            "row_count": len(coerced_rows),
            "critic_verdict": target_data.get("critic_verdict") if target_data else None
        }
