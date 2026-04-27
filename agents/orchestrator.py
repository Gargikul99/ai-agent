"""
orchestrator.py
Reads the manager's question and decides which agents to call.
Returns combined context for Gemma 4 to reason over.
"""

WAREHOUSE_KEYWORDS = [
    "stock","inventory","sku","reorder","stockout","warehouse","critical",
    "warning","healthy","supplier","replenish","days left","safety stock",
    "overstock","dead stock","category","zone"
]
TRANSPORT_KEYWORDS = [
    "carrier","lane","route","transit","on time","delivery performance",
    "cost per kg","damage","transport","mode","ftl","ltl","air","rail",
    "performance score","best carrier","worst carrier","freight"
]
SHIPMENT_KEYWORDS = [
    "shipment","order","delayed","in transit","held","lost","pod","proof",
    "delivery","dispatch","eta","fulfilment","fulfillment","customer",
    "out for delivery","tracking","sph","shp"
]

def route_question(question: str) -> dict:
    """Decide which agents are relevant for this question."""
    q = question.lower()
    return {
        "warehouse": any(k in q for k in WAREHOUSE_KEYWORDS),
        "transport":  any(k in q for k in TRANSPORT_KEYWORDS),
        "shipment":   any(k in q for k in SHIPMENT_KEYWORDS),
    }

def build_combined_context(question, routing,
                            wh_stats=None, wh_critical=None, wh_warning=None,
                            tr_stats=None, tr_delayed=None, tr_poor=None, tr_summ=None,
                            sh_stats=None, sh_delayed=None, sh_held=None, sh_lost=None):
    """Build a single combined prompt context from all relevant agents."""

    sections = []
    agents_used = []

    if routing["warehouse"] and wh_stats:
        agents_used.append("Warehouse")
        sections.append(f"""
WAREHOUSE DATA (Python-calculated):
- Total SKUs: {wh_stats['total_skus']} | Critical: {wh_stats['critical_count']} | Warning: {wh_stats['warning_count']} | Healthy: {wh_stats['healthy_count']}
- Most urgent SKU: {wh_stats['most_urgent_sku']} ({wh_stats['most_urgent_days']} days left)
- Total reorder units needed: {wh_stats['total_reorder_qty']:,}
- Categories at risk: {wh_stats['categories_at_risk']}

Critical SKUs:
{wh_critical.to_string(index=False) if wh_critical is not None else 'None'}

Warning SKUs (top 5):
{wh_warning.head(5).to_string(index=False) if wh_warning is not None else 'None'}
""")

    if routing["transport"] and tr_stats:
        agents_used.append("Transport")
        sections.append(f"""
TRANSPORT DATA (Python-calculated):
- Total lanes: {tr_stats['total_lanes']} | On time: {tr_stats['on_time_pct']}% | Delayed lanes: {tr_stats['delayed_lanes']}
- Avg delay: {tr_stats['avg_delay_days']} days | Poor performers: {tr_stats['poor_performers']} lanes
- Best carrier: {tr_stats['best_carrier']} | Worst carrier: {tr_stats['worst_carrier']}
- Avg cost/kg: INR {tr_stats['avg_cost_per_kg']} | Highest damage: {tr_stats['highest_damage_carrier']}

Delayed lanes:
{tr_delayed.to_string(index=False) if tr_delayed is not None else 'None'}

Poor performing lanes:
{tr_poor.to_string(index=False) if tr_poor is not None else 'None'}
""")

    if routing["shipment"] and sh_stats:
        agents_used.append("Shipment")
        sections.append(f"""
SHIPMENT DATA (Python-calculated):
- Total: {sh_stats['total_shipments']} | Delivered: {sh_stats['delivered']} | In transit: {sh_stats['in_transit']}
- Delayed: {sh_stats['delayed']} | Held at hub: {sh_stats['held_at_hub']} | Lost: {sh_stats['lost_in_transit']}
- Avg delay: {sh_stats['avg_delay_days']} days | Max delay: {sh_stats['max_delay_days']} days
- Value at risk: INR {sh_stats['total_value_at_risk']:,.0f}
- Most delayed carrier: {sh_stats['most_delayed_carrier']}
- Most affected customer: {sh_stats['most_affected_customer']}
- POD pending: {sh_stats['pod_pending']} shipments

Delayed shipments:
{sh_delayed.to_string(index=False) if sh_delayed is not None else 'None'}

Held at hub:
{sh_held.to_string(index=False) if sh_held is not None else 'None'}
""")

    if not sections:
        # fallback — use all agents if nothing matched
        agents_used = ["Warehouse","Transport","Shipment"]
        return build_combined_context(
            question,
            {"warehouse":True,"transport":True,"shipment":True},
            wh_stats,wh_critical,wh_warning,
            tr_stats,tr_delayed,tr_poor,tr_summ,
            sh_stats,sh_delayed,sh_held,sh_lost
        )

    combined = "\n".join(sections)
    return combined, agents_used
