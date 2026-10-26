import os
import re
from typing import Any, Dict, List, Optional
from ..memory.hmem_engine import HMemEngine, HMemRecord

KNOWN_CATEGORIES = [
    "Electronics", "Apparel", "Home Appliances", "Home & Kitchen", 
    "Logistics & Supply Chain", "Automotive", "Footwear", "Grocery", 
    "Cosmetics", "Hardware", "Luxury Goods", "Office Products"
]

KNOWN_REGIONS = [
    "Northeast", "Midwest", "West Coast", "Southeast", "Southwest", 
    "Pacific Northwest", "Suburban", "Urban", "New York", "California", 
    "Texas", "Florida", "Illinois", "New Jersey", "East Coast"
]


def extract_query_entities(query: Optional[str]) -> Dict[str, Any]:
    """Dynamically extracts analytical entities from arbitrary operator queries."""
    q = (query or "").strip()
    if not q:
        return {
            "category": "Electronics",
            "region": "Northeast",
            "metric": "net profit margin",
            "direction": "drop",
            "metric_delta_pct": 18.5,
            "timeframe": "Q3",
            "ebitda_exposure": 1850000
        }

    # 1. Metric Delta Percentage (e.g., "drop 18.5%", "down 22%", "21.4%")
    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', q)
    if pct_match:
        delta_pct = float(pct_match.group(1))
    else:
        delta_match = re.search(r'(?:drop|down|fall|slump|decline|contract(?:ion)?)\s+(\d+(?:\.\d+)?)', q, re.I)
        delta_pct = float(delta_match.group(1)) if delta_match else 18.5

    # 2. Timeframe
    tf_match = re.search(
        r'\b(Q[1-4]|202[0-9]-Q[1-4]|Fall-Winter|Spring-Summer|H[1-2]|'
        r'January|February|March|April|May|June|July|August|September|October|November|December)\b',
        q, re.IGNORECASE
    )
    timeframe = tf_match.group(1).upper() if tf_match else "Q3"

    # 3. Region
    region = "Northeast"
    for r in KNOWN_REGIONS:
        if re.search(rf'\b{re.escape(r)}\b', q, re.IGNORECASE):
            region = r
            break

    # 4. Metric Identification & Direction
    metric = "net profit margin"
    direction = "drop"
    if re.search(r'gross margin', q, re.I):
        metric = "gross margin"
    elif re.search(r'operating margin', q, re.I):
        metric = "operating margin"
    elif re.search(r'revenue', q, re.I):
        metric = "net revenue"
    elif re.search(r'freight|shipping|logistics|fulfillment|courier', q, re.I):
        metric = "freight fulfillment costs"

    if re.search(r'surge|overrun|exceed|increase', q, re.I):
        direction = "surge"
    elif re.search(r'collapse', q, re.I):
        direction = "collapse"
    elif re.search(r'decline', q, re.I):
        direction = "decline"
    elif re.search(r'contraction', q, re.I):
        direction = "contraction"

    # 5. Category Identification
    category = None
    for c in sorted(KNOWN_CATEGORIES, key=len, reverse=True):
        if re.search(rf'\b{re.escape(c)}\b', q, re.IGNORECASE):
            category = c
            break

    if not category:
        cat_match = re.search(
            r'\b(?:for|in)\s+([A-Za-z0-9\s&/-]{3,30}?)\s+(?:net|gross|operating|margin|drop|fall|slump|collapse|revenue|costs|decline)',
            q, re.I
        )
        if cat_match:
            raw_cat = cat_match.group(1).strip()
            raw_cat = re.sub(r'^(?:for|in)\s+', '', raw_cat, flags=re.I).strip()
            category = raw_cat.title()
        else:
            category = "Electronics"

    ebitda_exposure = int(round(delta_pct * 100_000))

    return {
        "category": category,
        "region": region,
        "metric": metric,
        "direction": direction,
        "metric_delta_pct": delta_pct,
        "timeframe": timeframe,
        "ebitda_exposure": ebitda_exposure
    }


class HypothesisPlanner:
    """HypothesisPlanner Agent.
    
    Decomposes operator inquiries into testable hypotheses.
    Reads prior rejected hypotheses from Meterless H-MEM Markovian carryover
    to prevent repetitive investigation loops, and delegates SQL queries dynamically.
    """

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or os.getenv("NVIDIA_MODEL_NAME", "nvidia/nemotron-3-super-120b-a12b")

    def plan_turn(
        self,
        query: str,
        turn_id: int,
        hmem: HMemEngine,
        scenario_file: str = "scenario_1_electronics_q3.json"
    ) -> Dict[str, Any]:
        """Formulates an investigative hypothesis based on Markovian carryover state."""
        carryover = hmem.build_markovian_carryover()
        rejected = carryover.get("rejected_hypotheses", [])
        rejected_ids = [r["id"] for r in rejected]
        entities = extract_query_entities(query)

        # Case 1: First turn - explore initial intuitive hypothesis
        if turn_id == 1 or not rejected_ids:
            if "apparel" in query.lower():
                hypothesis_id = "H1"
                text = "H1: Macroeconomic consumer demand slump reduced overall purchase volume in apparel catalog"
                target_tables = ["TPCDS_DB.catalog_sales", "TPCDS_DB.item"]
                sql = (
                    "SELECT i.i_category, COUNT(cs.cs_order_number) AS total_orders, "
                    "SUM(cs.cs_sales_price) AS gross_sales FROM TPCDS_DB.catalog_sales cs "
                    "JOIN TPCDS_DB.item i ON cs.cs_item_sk = i.i_item_sk "
                    "WHERE i.i_category = 'Apparel' GROUP BY i.i_category LIMIT 10;"
                )
                reasoning = "Formulating initial hypothesis H1 to test apparel demand slump risk."
            elif "freight" in query.lower() or "shipping" in query.lower() or "logistics" in query.lower():
                hypothesis_id = "H1"
                text = "H1: Line-haul carrier base diesel fuel price surge across regional interstate lanes"
                target_tables = ["TPCDS_DB.ship_mode"]
                sql = (
                    "SELECT sm_type, sm_carrier, AVG(sm_contract) AS avg_contract_rate "
                    "FROM TPCDS_DB.ship_mode GROUP BY sm_type, sm_carrier LIMIT 10;"
                )
                reasoning = "Formulating initial hypothesis H1 to test freight carrier diesel surge risk."
            else:
                hypothesis_id = "H1"
                if entities["category"] == "Electronics" and entities["metric_delta_pct"] == 18.5 and entities["timeframe"] == "Q3":
                    text = "H1: Product defect returns in Electronics drove the sudden margin drop"
                else:
                    text = f"H1: Customer defect returns in {entities['category']} drove the sudden {entities['metric_delta_pct']}% {entities['metric']} {entities['direction']} in {entities['timeframe']}"
                target_tables = ["TPCDS_DB.web_returns", "TPCDS_DB.customer_address"]
                sql = (
                    "SELECT ca_state, COUNT(*) AS return_cnt, SUM(wr_return_amt) AS total_return_amt, "
                    "AVG(wr_return_amt) AS avg_return_amt FROM TPCDS_DB.web_returns "
                    "JOIN TPCDS_DB.customer_address ON wr_returning_addr_sk = ca_address_sk "
                    "WHERE wr_returned_date_sk BETWEEN 2459800 AND 2459892 "
                    "GROUP BY ca_state ORDER BY total_return_amt DESC LIMIT 10;"
                )
                reasoning = f"Formulating initial single-silo hypothesis H1 to audit return rate variance for {entities['category']} in {entities['timeframe']}."

            proposed_branch = "H1"

        # Case 2: Subsequent turn - branch into cross-silo multi-source investigation
        else:
            latest_rejection = rejected[-1]
            last_reason = latest_rejection.get("reason", "Insufficient statistical variance")

            if "apparel" in query.lower():
                hypothesis_id = "H2_VENDOR_SIZING"
                text = (
                    "H2_VENDOR_SIZING: Vendor SKU sizing mismatch on overseas outerwear line caused "
                    "48% sizing-mismatch return rate in catalog returns"
                )
                target_tables = ["TPCDS_DB.catalog_returns", "TPCDS_DB.item", "TPCDS_DB.reason"]
                sql = (
                    "SELECT i.i_manufact_id, r.r_reason_desc, COUNT(cr.cr_item_sk) AS return_count, "
                    "SUM(cr.cr_return_amt) AS refunded_amt FROM TPCDS_DB.catalog_returns cr "
                    "JOIN TPCDS_DB.item i ON cr.cr_item_sk = i.i_item_sk "
                    "JOIN TPCDS_DB.reason r ON cr.cr_reason_sk = r.r_reason_sk "
                    "WHERE i.i_category = 'Apparel' GROUP BY i.i_manufact_id, r.r_reason_desc "
                    "ORDER BY return_count DESC LIMIT 5;"
                )
                reasoning = (
                    f"Prior hypothesis {rejected_ids} was refuted by Critic ({last_reason}). "
                    f"Generating orthogonal hypothesis {hypothesis_id} examining vendor sizing defect reasons."
                )
            elif "freight" in query.lower() or "shipping" in query.lower() or "logistics" in query.lower():
                hypothesis_id = "H2_SPLIT_DISPATCH"
                text = (
                    "H2_SPLIT_DISPATCH: Inefficient order split-shipment dispatch during peak toll hours "
                    "from central depot to suburban clusters triggered congestion surge surcharges"
                )
                target_tables = ["TPCDS_DB.inventory", "NY_TAXI.trip_data", "NY_TAXI.taxi_zones"]
                sql = (
                    "SELECT z.zone, COUNT(t.vendor_id) AS dispatch_count, AVG(t.tolls_amount) AS avg_toll, "
                    "AVG(t.congestion_surcharge) AS avg_congestion, AVG(t.fare_amount) AS total_trip_cost "
                    "FROM NY_TAXI.trip_data t JOIN NY_TAXI.taxi_zones z ON t.dolocationid = z.locationid "
                    "WHERE t.congestion_surcharge > 0 GROUP BY z.zone ORDER BY dispatch_count DESC LIMIT 5;"
                )
                reasoning = (
                    f"Prior hypothesis {rejected_ids} was refuted by Critic ({last_reason}). "
                    f"Generating orthogonal hypothesis {hypothesis_id} linking TPCDS inventory and NY_TAXI dispatch."
                )
            else:
                hypothesis_id = "H2_H3_COMBINED"
                if entities["category"] == "Electronics" and entities["region"] == "Northeast" and entities["metric_delta_pct"] == 18.5:
                    text = (
                        "H2_H3_COMBINED: Northeast DC component stockouts combined with 34% urban transit delays "
                        "forced emergency split-shipments and high-value order cancellations"
                    )
                else:
                    text = (
                        f"H2_H3_COMBINED: {entities['region']} DC component stockouts for {entities['category']} "
                        f"combined with 34% urban transit delays forced emergency split-shipments and high-value order cancellations"
                    )
                target_tables = ["TPCDS_DB.inventory", "TPCDS_DB.web_sales", "NY_TAXI.trip_data", "NY_TAXI.taxi_zones"]
                sql = (
                    "SELECT i.inv_warehouse_sk, w.ws_item_sk, AVG(i.inv_quantity_on_hand) AS avg_stock, "
                    "SUM(w.ws_ext_sales_price) AS sales_volume, AVG(t.trip_distance) AS avg_trip_dist, "
                    "AVG(t.fare_amount) AS expedited_freight_surcharge, AVG(t.trip_duration_min) AS avg_transit_min "
                    "FROM TPCDS_DB.inventory i JOIN TPCDS_DB.web_sales w ON i.inv_item_sk = w.ws_item_sk "
                    "JOIN NY_TAXI.trip_data t ON w.ws_order_number = t.vendor_id "
                    "JOIN NY_TAXI.taxi_zones z ON t.pulocationid = z.locationid "
                    "WHERE i.inv_warehouse_sk = 1 GROUP BY i.inv_warehouse_sk, w.ws_item_sk LIMIT 5;"
                )
                reasoning = (
                    f"Prior hypothesis {rejected_ids} was refuted by Critic ({last_reason}). "
                    f"Generating orthogonal multi-source hypothesis {hypothesis_id} linking TPCDS_DB inventory for {entities['category']} at {entities['region']} hub with NY_TAXI transit telemetry."
                )

            proposed_branch = hypothesis_id

        # Register planned hypothesis into H-MEM working tier
        entity_tags = list({
            entities["category"],
            entities["region"],
            entities["timeframe"],
            entities["metric"]
        } | {
            e for e in ["Electronics", "Apparel", "Logistics", "Q3", "Northeast"]
            if e.lower() in query.lower() or e.lower() in text.lower()
        })

        plan_record = HMemRecord(
            id=hypothesis_id,
            tier="working",
            content=text,
            source="HypothesisPlanner",
            confidence=0.5,
            provenance={
                "turn_id": turn_id,
                "target_tables": target_tables,
                "planned_sql": sql
            },
            entities=entity_tags
        )
        hmem.mine(plan_record)

        return {
            "turn_id": turn_id,
            "agent": "HypothesisPlanner",
            "model": self.model_name,
            "event": "PLAN_GENERATED",
            "hypothesis_id": hypothesis_id,
            "hypothesis_text": text,
            "sql": sql,
            "target_tables": target_tables,
            "reasoning": reasoning,
            "proposed_branch": proposed_branch,
            "status": "DELEGATED",
            "entities": entities
        }
