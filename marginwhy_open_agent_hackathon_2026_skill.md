---
name: open-agent-hackathon-2026-marginwhy
description: Comprehensive technical skill and BTC reference specification for coding agents (Cursor, Codex, Claude) building MarginWhy for team Light of Numbers in the Open Agent Hackathon 2026. Covers Zetaris Lightning SQL and REST/JDBC adapters, Meterless H-MEM hierarchical memory and Markovian carryover, Meterless Nightshift and NVIDIA Nemotron routing, and non-linear multi-agent critic loops.
---

# Open Agent Hackathon 2026 — Agent Technical Skill (`SKILL.md`)

Tài liệu kỹ năng (`SKILL.md` / `AGENTS.md`) này tổng hợp toàn bộ quy chuẩn kỹ thuật, cú pháp câu lệnh, biến môi trường, giao thức kết nối và mẫu mã nguồn chính thức từ Ban Tổ Chức **[Open Agent Hackathon 2026](https://hackathon.genai.works/event/open-agent-hackathon-2026)**, kho mã nguồn **[Zetaris Getting Started](https://github.com/zetaris/getting-started)**, kiến trúc bộ nhớ **[Meterless H-MEM](https://github.com/Meterless/H-MEM)** và nền tảng **[Meterless Nightshift](https://meterless.ai/engines.html)**. Đặt tệp này tại thư mục gốc của dự án (`SKILL.md` hoặc `AGENTS.md`) hoặc trong `.cursor/rules/` để AI Coding Agent tuân thủ chính xác các tiêu chuẩn chấm điểm.

## 1. Khi Nào Cần Kích Hoạt Bộ Kỹ Năng Này (Trigger Scenarios)

* Khởi tạo hoặc chỉnh sửa mã nguồn dự án **MarginWhy** (Đội **Light of Numbers**) cho hạng mục **Track 02: The Agent That Can Explain Why**.
* Viết adapter kết nối tới **Zetaris AI Data Harness** qua giao thức Direct REST, UI Proxy hoặc JDBC để truy vấn hai bộ dữ liệu mẫu `TPCDS_DB` và `NY_TAXI`.
* Triển khai bộ máy bộ nhớ phân cấp **Meterless `H-MEM`**, cơ chế nén ngữ cảnh **Markovian Engine** và viết bài kiểm thử hợp chuẩn (`tests/test_hmem_conformance.py`).
* Cấu hình lệnh gọi suy luận qua **Meterless Nightshift** tới mô hình **NVIDIA Nemotron** (`nvidia/nemotron-3-super-120b-a12b`).
* Xây dựng vòng lặp phản biện phi tuyến tính (`HypothesisPlanner` -> `ZetarisRetriever` -> `SkepticalCritic` -> `ActionReportWriter`) và xuất nhật ký truy vết `logs/trace.jsonl`.

## 2. Kỹ Năng 1: Làm Chủ Tầng Dữ Liệu Zetaris & Ngôn Ngữ Lightning SQL

Nguồn tham chiếu chính thức từ BTC: **[Zetaris Client Setup](https://github.com/zetaris/getting-started/blob/main/docs/connections/client-setup.md)**, **[Lightning Recipe Reference](https://github.com/zetaris/getting-started/blob/main/docs/connections/lightning-recipe-reference.md)** và **[Scripts HOWTO](https://github.com/zetaris/getting-started/blob/main/scripts/HOWTO.md)**.

### 2.1. Biến Môi Trường Chuẩn Cho Zetaris (`.env` / `.env.local`)

Lưu toàn bộ thông tin xác thực trong tệp `.env` hoặc `.env.local` (bắt buộc đưa vào `.gitignore`). Tuyệt đối không đưa khóa API hoặc mật khẩu vào prompt, mã nguồn hay lịch sử commit.

| Biến Môi Trường | Giao Thức Sử Dụng | Giá Trị Chuẩn & Quy Tắc Cấu Hình Từ BTC |
| :--- | :--- | :--- |
| `ZETARIS_REST_URL` | Direct REST API | Đường dẫn gốc kết thúc bằng `/api/v1.0` (mặc định local: `http://localhost:8888/api/v1.0`). |
| `ZETARIS_BASE_URL` | UI Proxy Helpers | Địa chỉ gốc của Web UI không kèm đường dẫn con (mặc định local: `http://localhost:3000`). |
| `ZETARIS_ORG_ID` | Cả Direct REST & UI Proxy | Mã số nguyên (numeric ID) lấy tại `Management -> Organisation` trên giao diện Zetaris (ví dụ: `1`). Không dùng tên chữ hay slug. |
| `ZETARIS_API_KEY` | Cả Direct REST & UI Proxy | Khóa API tạo tại `Management -> API Tokens`. Nếu gặp lỗi HTTP `401`, cần tạo lại khóa mới trên GUI. |
| `ZETARIS_QUERY_LIMIT` | UI Proxy Query Helper | Giới hạn số dòng trả về tối đa cho mỗi truy vấn (mặc định: `1000`). |
| `ZETARIS_ENGINE_ID` | UI Proxy Query Helper | Mã định danh compute engine (tùy chọn). |
| `ZETARIS_JDBC_URL` | JDBC Driver | Chuỗi kết nối JDBC (mặc định local: `jdbc:zetaris:lightning@localhost:10000`). |
| `ZETARIS_JDBC_JAR` | JDBC Driver | Đường dẫn tuyệt đối tới tệp `.jar` của Zetaris JDBC driver (yêu cầu JDK 11 trở lên). |
| `ZETARIS_USERNAME` | JDBC / OpenAPI Spec | Tài khoản đăng nhập Zetaris. |
| `ZETARIS_PASSWORD` | JDBC / OpenAPI Spec | Mật khẩu đăng nhập Zetaris. |

### 2.2. Cú Pháp Zetaris Lightning SQL Bắt Buộc Phải Nhớ

Zetaris sử dụng phương ngữ **Lightning SQL**. Khi viết câu lệnh cho `ZetarisRetriever`, tác tử phải tuân thủ các lệnh đặc thù sau:

```sql
-- 1. Kiểm tra kết nối và phiên bản máy chủ Zetaris
SELECT 1 AS one;
SHOW SERVER VERSION;

-- 2. Khám phá cơ sở dữ liệu mẫu (QUAN TRỌNG: NY_TAXI và TPCDS_DB là filestore/REST nên nằm ở LIGHTNING DATABASES, KHÔNG nằm ở SHOW DATASOURCES)
SHOW LIGHTNING DATABASES;

-- 3. Liệt kê danh sách các bảng trong từng cơ sở dữ liệu mẫu
SHOW LIGHTNING TABLES NY_TAXI;
SHOW LIGHTNING TABLES TPCDS_DB;

-- 4. Kiểm tra cấu trúc cột (Schema Inspection) trước khi viết câu lệnh JOIN
DESCRIBE DATASOURCE TABLE NY_TAXI.taxi_zones;
DESCRIBE DATASOURCE TABLE TPCDS_DB.reason;

-- 5. Truy vấn dữ liệu mẫu với tên bảng đầy đủ (<database>.<table>) và luôn kèm LIMIT
SELECT * FROM NY_TAXI.taxi_zones LIMIT 5;
SELECT r_reason_sk, r_reason_desc FROM TPCDS_DB.reason ORDER BY r_reason_sk LIMIT 5;
```

### 2.3. Năm Quy Tắc Vàng Khi Gọi Zetaris Từ AI Agent

1. **Một câu lệnh mỗi lượt gọi (Single Statement per Request):** Chỉ gửi đúng 1 câu lệnh SQL trong mỗi lời gọi API hoặc JDBC. Không ghép nhiều câu lệnh cách nhau bằng dấu chấm phẩy `;` (ngoại trừ khối lệnh `COMPILE USL` đa bảng phải giữ nguyên khối).
2. **Ép kiểu dữ liệu trả về từ REST (String-to-Float Parsing):** Giao thức Zetaris REST trả mọi giá trị số và số thập phân (kể cả dạng số mũ khoa học như `1.85e-01`) dưới dạng **chuỗi ký tự (`string`)**. Trước khi đưa vào `SkepticalCritic` tính toán thống kê, adapter bắt buộc phải ép kiểu sang `float` hoặc `int`.
3. **Header bắt buộc cho REST / UI Proxy:** Mọi yêu cầu HTTP tới Zetaris phải đính kèm `Authorization: Bearer <ZETARIS_API_KEY>`, header `X-Org-ID: <ZETARIS_ORG_ID>` (dạng số) và tạo mới một mã UUIDv4 cho `X-Request-ID` (và `queryId`) ở từng lượt gọi.
4. **Cài đặt `timeout=30` giây và tránh nguồn lỗi đã biết:** Mọi truy vấn Zetaris phải đặt `timeout=30` giây. Nếu kết nối các nguồn mở rộng, tránh nguồn `03_pudl_create.sql` (đã được BTC xác nhận lỗi do tên S3 bucket `pudl.catalyst.coop` chứa dấu chấm); với nguồn giới hạn tần suất như `12_company_dns_create.sql`, phải giãn cách tối thiểu 15 giây giữa các lệnh và chờ 60 giây nếu gặp mã lỗi HTTP `429`.
5. **Chế độ dự phòng `SAMPLE_MODE=true`:** Khi biến môi trường `SAMPLE_MODE=true` hoặc khi Zetaris trả lỗi `UpstreamTimeout` / `ConnectionError`, adapter phải lập tức chuyển sang đọc dữ liệu từ `data/samples/*.json` để không bao giờ làm treo chương trình khi giám khảo chấm tự động.

### 2.4. Mẫu Code Chuẩn Cho `app/adapters/zetaris_adapter.py`

```python
import json
import os
import time
import uuid
from typing import Any, Dict, List
import urllib.request
import urllib.error


class ZetarisAdapter:
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
        """Zetaris REST returns numeric/decimal values as strings (including exponent notation)."""
        coerced: Dict[str, Any] = {}
        for k, v in row.items():
            if isinstance(v, str):
                try:
                    coerced[k] = int(v)
                    continue
                except ValueError:
                    pass
                try:
                    coerced[k] = float(v)
                    continue
                except ValueError:
                    pass
            coerced[k] = v
        return coerced

    def execute_sql(self, sql: str, hypothesis_id: str, scenario_file: str = "scenario_1_electronics_q3.json") -> Dict[str, Any]:
        clean_sql = sql.strip().rstrip(";")
        if "LIMIT" not in clean_sql.upper() and clean_sql.upper().startswith("SELECT"):
            clean_sql = f"{clean_sql} LIMIT {self.query_limit}"

        if self.sample_mode or not self.api_key:
            return self._load_sample_fallback(hypothesis_id, clean_sql, scenario_file, reason="SAMPLE_MODE_ACTIVE")

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
            req = urllib.request.Request(f"{self.base_url}/api/proxy/query", data=payload, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                    raw_data = json.loads(resp.read().decode("utf-8"))
                    rows = [self._coerce_numeric_row(r) for r in raw_data.get("rows", [])]
                    return {
                        "status": "SUCCESS",
                        "source": "ZETARIS_LIVE",
                        "request_id": req_id,
                        "sql": clean_sql,
                        "rows": rows
                    }
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 2:
                    return self._load_sample_fallback(hypothesis_id, clean_sql, scenario_file, reason=f"UpstreamTimeout: {exc}")
                time.sleep(1.5)

        return self._load_sample_fallback(hypothesis_id, clean_sql, scenario_file, reason="Fallback")

    def _load_sample_fallback(self, hypothesis_id: str, sql: str, scenario_file: str, reason: str) -> Dict[str, Any]:
        sample_path = os.path.join("data", "samples", scenario_file)
        with open(sample_path, "r", encoding="utf-8") as f:
            bundle = json.load(f)
        rows: List[Dict[str, Any]] = bundle.get("queries", {}).get(hypothesis_id, {}).get("rows", [])
        return {
            "status": "FALLBACK_SAMPLE",
            "fallback_reason": reason,
            "source": f"LOCAL_SAMPLE:{scenario_file}",
            "sql": sql,
            "rows": [self._coerce_numeric_row(r) for r in rows]
        }
```

## 3. Kỹ Năng 2: Triển Khai Bộ Nhớ Phân Cấp Meterless `H-MEM` & `Markovian` Carryover

Nguồn tham chiếu chính thức: **[Meterless H-MEM Specification](https://github.com/Meterless/H-MEM)**, **[Meterless Context Stack](https://github.com/Meterless/Meterless)** và **[Đánh giá Kiến trúc 4 Engine của Meterless](https://wavect.io/blog/meterless-ai-agent-context-layer-review/)**.

### 3.1. Kiến Trúc & Hợp Đồng Dữ Liệu Của `H-MEM` (Hierarchical Memory)

Khác với cơ sở dữ liệu vector thông thường chỉ lưu văn bản tóm tắt, **Meterless `H-MEM`** hoạt động như một đồ thị tri thức sống có truy nguyên nguồn gốc (living knowledge graph with provenance):

* **Phân tầng bộ nhớ (3 Tiers):**
  * `short_term` (Episodic Tier): Lưu nhật ký từng bước thực thi, câu lệnh SQL vừa chạy và dữ liệu thô trả về trong phiên hiện tại.
  * `working` (Semantic Working Tier): Lưu trạng thái các giả thuyết đang điều tra (`H1`, `H2`, `H3`), điểm số `confidence_score` và phán quyết từ `SkepticalCritic`.
  * `long_term` (Procedural & Consolidated Tier): Lưu các quy tắc nghiệp vụ đã được xác thực, các mẫu sửa lỗi SQL và danh sách các giả thuyết đã bị bác bỏ để không bao giờ lặp lại.
* **Hợp đồng trường dữ liệu bắt buộc (Mandatory Record Schema):** Mọi bản ghi trong `H-MEM` phải có đủ 8 trường:
  * `id`: Mã định danh duy nhất của bản ghi nhớ.
  * `tier`: Một trong 3 giá trị `short_term`, `working`, hoặc `long_term`.
  * `source`: Tác tử hoặc nguồn dữ liệu tạo ra bản ghi (ví dụ: `SkepticalCritic`, `Zetaris_TPCDS_DB`).
  * `confidence`: Điểm tin cậy từ `0.0` đến `1.0`.
  * `provenance`: Thông tin truy nguyên (chứa `turn_id`, `sql_query`, `table_names`, `timestamp`).
  * `entities`: Danh sách thực thể liên quan (ví dụ: `["Electronics", "Q3_2026", "Northeast_Warehouse"]`).
  * `relationships`: Các cạnh quan hệ đồ thị (ví dụ: `[{"from": "H1", "type": "REFUTED_BY", "to": "TPCDS_DB.web_returns"}]`).
  * `replacement_lineage`: Lưu vết giả thuyết mới nào được sinh ra để thay thế giả thuyết cũ vừa bị bác bỏ (ví dụ: `{"superseded_id": "H1", "replaced_by": "H2_H3_COMBINED"}`).
* **Sổ cái kiểm toán (`trust_ledger`):** Mọi thao tác thêm mới, cập nhật điểm tin cậy hoặc bác bỏ giả thuyết đều phải ghi vào một danh sách bất biến (`trust_ledger`) để kiểm toán viên hoặc giám khảo truy vết.
* **Nguyên lý `Markovian` Bounded Carryover:** Không nối toàn bộ lịch sử hội thoại dài hàng chục nghìn token vào prompt của mỗi bước. Ở mỗi vòng lặp, chỉ truyền vào Agent: *(1) Mục tiêu cố định + (2) Đầu vào bước hiện tại + (3) Bản tóm tắt trạng thái rút gọn (`bounded_carryover`) trích xuất từ `H-MEM`*.

### 3.2. Mẫu Code Chuẩn Cho `app/memory/hmem_engine.py`

```python
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class HMemRecord:
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


class HMemEngine:
    """Reference implementation of Meterless H-MEM with provenance, hybrid retrieval, and trust ledger."""

    def __init__(self) -> None:
        self.records: Dict[str, HMemRecord] = {}
        self.trust_ledger: List[Dict[str, Any]] = []

    def mine(self, record: HMemRecord) -> HMemRecord:
        self.records[record.id] = record
        self._audit("MINE", record.id, {"tier": record.tier, "confidence": record.confidence, "status": record.status})
        return record

    def reject_and_branch(self, rejected_id: str, new_id: str, reason: str, critic_confidence: float) -> None:
        if rejected_id in self.records:
            rec = self.records[rejected_id]
            rec.status = "REJECTED"
            rec.confidence = critic_confidence
            rec.replacement_lineage = {"superseded_id": rejected_id, "replaced_by": new_id, "reason": reason}
            self._audit("CLAIM_BLOCKED_LINEAGE", rejected_id, rec.replacement_lineage)

    def retrieve_hybrid(self, query_entities: List[str], min_confidence: float = 0.0, include_rejected: bool = False) -> List[HMemRecord]:
        results: List[tuple[float, HMemRecord]] = []
        for rec in self.records.values():
            if not include_rejected and rec.status == "REJECTED":
                continue
            if rec.confidence < min_confidence:
                continue
            entity_overlap = len(set(query_entities).intersection(set(rec.entities)))
            tier_weight = 1.2 if rec.tier == "working" else (1.1 if rec.tier == "long_term" else 1.0)
            score = (rec.confidence * 0.6) + (entity_overlap * 0.3) * tier_weight
            results.append((score, rec))
        results.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in results]

    def get_rejected_hypotheses(self) -> List[str]:
        return [r.id for r in self.records.values() if r.status == "REJECTED"]

    def build_markovian_carryover(self) -> Dict[str, Any]:
        """Produces a bounded state summary so agents never re-read full raw transcripts."""
        return {
            "rejected_hypotheses": [
                {"id": r.id, "reason": (r.replacement_lineage or {}).get("reason", ""), "confidence": r.confidence}
                for r in self.records.values() if r.status == "REJECTED"
            ],
            "approved_claims": [
                {"id": r.id, "content": r.content, "confidence": r.confidence, "provenance": r.provenance}
                for r in self.records.values() if r.status == "ACTIVE" and r.confidence >= 0.70
            ],
            "ledger_mutations": len(self.trust_ledger)
        }

    def consolidate_sleep_cycle(self) -> int:
        """Promotes verified working memories (confidence >= 0.70) into long_term tier."""
        promoted = 0
        for rec in self.records.values():
            if rec.tier == "working" and rec.status == "ACTIVE" and rec.confidence >= 0.70:
                rec.tier = "long_term"
                rec.status = "CONSOLIDATED"
                promoted += 1
                self._audit("CONSOLIDATE", rec.id, {"new_tier": "long_term"})
        return promoted

    def _audit(self, action: str, record_id: str, details: Dict[str, Any]) -> None:
        self.trust_ledger.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "record_id": record_id,
            "details": details
        })
```

## 4. Kỹ Năng 3: Định Tuyến Suy Luận Qua Meterless Nightshift & NVIDIA Nemotron

Nguồn tham chiếu chính thức: **[Meterless Engines API (`meterless.ai/engines.html`)](https://meterless.ai/engines.html)** và **[Thể lệ Giải thưởng NVIDIA Nemotron](https://hackathon.genai.works/event/open-agent-hackathon-2026)**.

### 4.1. Hai Phương Thức Kết Nối Meterless Nightshift

1. **Phương thức Chuẩn OpenAI SDK (Khuyến nghị cho vòng lặp Agent thời gian thực):**
   * Cấu hình client trỏ về `METERLESS_BASE_URL` (ví dụ: `http://localhost:11434/v1` hoặc endpoint đám mây do BTC cấp) với `api_key=os.getenv("METERLESS_API_KEY")`.
   * Đặt tên mô hình mặc định là `nvidia/nemotron-3-super-120b-a12b` (cho phép ghi đè qua biến môi trường `NVIDIA_MODEL_NAME`).
   * Ghi rõ chuỗi `"model": "nvidia/nemotron-3-super-120b-a12b"` vào mọi dòng sự kiện trong `logs/trace.jsonl` để ban giám khảo xác nhận điều kiện trao giải **NVIDIA DGX Spark ($4,699)**.
2. **Phương thức Nightshift Job Queue API (`/v1/jobs` — Dành cho xử lý lô/kiểm chứng đa nhánh):**
   * Theo tài liệu **[Meterless Engines](https://meterless.ai/engines.html)**, khi gọi trực tiếp REST API của Nightshift:
     * Bước 1: Gửi `POST /v1/jobs` với payload `{ "kind": "best_of_n", "app": "MarginWhy", "mode": "meterless/text", "n": 1, "window": "now", "privacy": "cloud-ok", "media_autopilot": {"mode": "off"}, "messages": [...] }`. Lưu ý: Không bao giờ tự ý mở rộng mức `privacy` (`local-only`, `edge-only`, `cloud-ok`) vượt quá cấu hình của người dùng.
     * Bước 2: Thăm dò `GET /v1/jobs/{id}` cho đến khi `generated > 0`, sau đó đọc `GET /v1/jobs/{id}/attempts` (hoặc đọc `winner_seq` rồi gọi `GET /v1/jobs/{id}/attempts/{seq}`). Tuyệt đối không mặc định lấy `seq 1` mà phải kiểm tra `winner_seq` không có lỗi.

## 5. Kỹ Năng 4: Điều Phối Vòng Lặp Phản Biện & Kiểm Chứng Đầu Ra

Để đạt điểm tối đa ở **Track 02 (The Agent That Can Explain Why)**, bộ điều phối `app/agents/orchestrator.py` phải thực thi chu trình kiểm duyệt nghiêm ngặt sau:

1. **Khởi tạo & Đọc Bộ Nhớ (`Turn 1 - Plan`):** `HypothesisPlanner` đọc `hmem.build_markovian_carryover()`, phát hiện danh sách giả thuyết đã bị bác bỏ đang rỗng, sinh giả thuyết ban đầu `H1` (ví dụ: tỷ lệ trả hàng tăng) và ghi sự kiện `PLAN_GENERATED` vào `logs/trace.jsonl`.
2. **Truy vấn Zetaris (`Turn 1 - Retrieve`):** `ZetarisRetriever` tạo câu lệnh Lightning SQL truy vấn `TPCDS_DB.web_returns`, gọi `zetaris_adapter.execute_sql()`, lưu kết quả vào tầng `short_term` của `H-MEM` và ghi sự kiện `ZETARIS_QUERY_EXECUTED`.
3. **Phản biện & Chặn Kết Luận Yếu (`Turn 1 - Critique`):** `SkepticalCritic` (chạy trên `nvidia/nemotron-3-super-120b-a12b`) phân tích số liệu, phát hiện mức tăng trả hàng 1.2% không giải thích được mức sụt giảm 18.5% biên lợi nhuận (`confidence_score = 0.42 < 0.70`). Critic bắt buộc:
   * Phát sự kiện `CLAIM_BLOCKED` kèm trạng thái `BRANCH_RETRY` vào `logs/trace.jsonl`.
   * Gọi `hmem.reject_and_branch("H1", "H2_H3_COMBINED", reason, 0.42)` để khóa vĩnh viễn `H1`.
4. **Rẽ Nhánh & Truy Vấn Liên Nguồn (`Turn 2 - Branch & Verify`):** `HypothesisPlanner` đọc lại carryover từ `H-MEM`, thấy `H1` đã bị bác bỏ nên tự động chuyển sang giả thuyết liên nguồn `H2_H3_COMBINED` (kết hợp bảng tồn kho `TPCDS_DB.inventory`, doanh số `TPCDS_DB.web_sales` và độ trễ giao vận `NY_TAXI`). `SkepticalCritic` kiểm định bằng chứng mới đạt `confidence_score = 0.91 >= 0.70` và phát sự kiện `APPROVED_CLAIM`.
5. **Hợp Nhất Bộ Nhớ & Xuất Báo Cáo (`Consolidate & Synthesize`):** Gọi `hmem.consolidate_sleep_cycle()` để nâng cấp phát hiện đã duyệt lên tầng `long_term`, sau đó `ActionReportWriter` xuất báo cáo giải thích rõ "Tại sao", trích dẫn đúng tên bảng/số liệu và liệt kê mục `Caveats & Data Limitations`.

## 6. Các Lệnh Kiểm Tra Bắt Buộc Trước Khi Hoàn Tất (Verification Commands)

Sau khi viết code xong, AI Coding Agent bắt buộc phải chạy và xác nhận thành công 4 câu lệnh kiểm tra dưới đây trên terminal:

```bash
# 1. Chạy bộ kiểm thử hợp chuẩn H-MEM và luồng phản biện Critic
pytest tests/test_hmem_conformance.py -v

# 2. Chạy thử toàn bộ hệ thống ở chế độ Clean Clone (Sample Mode, không cần API key)
python3 run.py --query "Why did net profit margin for Electronics drop 18.5% in Q3?" --sample-mode

# 3. Kiểm tra tệp log JSONL có chứa đầy đủ sự kiện CLAIM_BLOCKED, BRANCH_RETRY và tên model NVIDIA Nemotron
python3 -c '
import json
with open("logs/trace.jsonl", "r", encoding="utf-8") as f:
    events = [json.loads(line) for line in f if line.strip()]
assert any(e.get("event") == "CLAIM_BLOCKED" for e in events), "Missing CLAIM_BLOCKED event!"
assert any("nemotron" in str(e.get("model", "")).lower() for e in events), "Missing NVIDIA Nemotron model tag!"
print("Trace verification passed! Total events:", len(events))
'

# 4. Kiểm tra an toàn bảo mật trước khi git commit (đảm bảo không lộ file .env)
git status --ignored
```

## 7. Các Lỗi Thường Gặp Cần Tránh (Gotchas)

* **Lỗi tìm không thấy bảng `NY_TAXI` hoặc `TPCDS_DB`:** Đừng chạy `SHOW DATASOURCES;` để tìm hai bộ dữ liệu này vì chúng là filestore mẫu của Zetaris; luôn dùng `SHOW LIGHTNING DATABASES;` và truy vấn có tiền tố `NY_TAXI.<ten_bang>` hoặc `TPCDS_DB.<ten_bang>`.
* **Lỗi `TypeError` khi so sánh số liệu từ Zetaris REST:** Dữ liệu số từ Zetaris REST API luôn ở dạng chuỗi (`"18.5"` hoặc `"1.2e+02"`). Luôn gọi hàm ép kiểu `_coerce_numeric_row()` trước khi tính toán.
* **Lỗi HTTP `400 Bad Request` trên Zetaris REST:** Xảy ra khi thiếu header `X-Org-ID` dạng số nguyên hoặc khi `X-Request-ID` / `queryId` không phải là một chuỗi UUID hợp lệ.
* **Lỗi lặp vô hạn giữa Planner và Critic:** Luôn giới hạn vòng lặp điều tra tối đa `MAX_TURNS = 3` trong `orchestrator.py` và bắt buộc `HypothesisPlanner` phải đọc `hmem.get_rejected_hypotheses()` trước khi lập kế hoạch mới.
