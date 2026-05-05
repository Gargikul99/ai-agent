import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def get_engine():
    return create_engine(
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )

DELAY_THRESHOLD_DAYS = 2
HIGH_VALUE_THRESHOLD = 50000

def get_shipments(zone_ids=None, status_filter=None):
    # ── individual shipment detail — stays on raw table ──
    # needs lane join and individual shipment fields not in zone_summary
    conditions = []
    params     = []

    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        conditions.append(f"s.zone_id IN ({placeholders})")
        params.extend(zone_ids)

    if status_filter:
        placeholders = ",".join(["%s"] * len(status_filter))
        conditions.append(f"s.status IN ({placeholders})")
        params.extend(status_filter)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
        SELECT
            s.shipment_id, s.order_id, s.zone_id,
            s.origin, s.customer, s.category,
            s.carrier, s.status, s.dispatch_date,
            s.planned_delivery, s.actual_delivery,
            s.delay_days, s.weight_kg, s.value_usd,
            s.pod_received, s.last_updated,
            z.city, z.region,
            t.performance_score AS lane_performance,
            t.mode              AS transport_mode,
            t.distance_km
        FROM shipments s
        JOIN zones z ON s.zone_id = z.zone_id
        LEFT JOIN transport t ON s.lane_id = t.lane_id
        {where}
        ORDER BY s.delay_days DESC, s.value_usd DESC
    """

    df = pd.read_sql(query, get_engine(),
                     params=tuple(params) if params else None)
    return df

def get_shipment_stats(zone_ids=None):
    df = get_shipments(zone_ids)

    delayed    = df[df["status"] == "Delayed"]
    held       = df[df["status"] == "Held at Hub"]
    lost       = df[df["status"] == "Lost in Transit"]
    in_transit = df[df["status"] == "In Transit"]
    delivered  = df[df["status"] == "Delivered"]
    out_del    = df[df["status"] == "Out for Delivery"]
    pod_pend   = df[(df["status"] == "Delivered") &
                    (df["pod_received"] == False)]
    high_value_at_risk = df[
        (df["status"].isin(["Delayed","Held at Hub","Lost in Transit"])) &
        (df["value_usd"] > HIGH_VALUE_THRESHOLD)
    ]

    value_at_risk = round(
        delayed["value_usd"].sum() +
        held["value_usd"].sum() +
        lost["value_usd"].sum(), 2
    )

    most_affected        = delayed["customer"].value_counts().index[0] \
                           if len(delayed) > 0 else "None"
    most_delayed_carrier = delayed["carrier"].value_counts().index[0] \
                           if len(delayed) > 0 else "None"

    stats = {
        "total_shipments":        len(df),
        "delivered":              len(delivered),
        "in_transit":             len(in_transit),
        "out_for_delivery":       len(out_del),
        "delayed":                len(delayed),
        "held_at_hub":            len(held),
        "lost_in_transit":        len(lost),
        "pod_pending":            len(pod_pend),
        "avg_delay_days":         round(delayed["delay_days"].mean(), 1) if len(delayed) > 0 else 0,
        "max_delay_days":         int(delayed["delay_days"].max())        if len(delayed) > 0 else 0,
        "value_at_risk":          value_at_risk,
        "high_value_at_risk":     len(high_value_at_risk),
        "most_affected_customer": most_affected,
        "most_delayed_carrier":   most_delayed_carrier,
        "on_time_delivery_pct":   round(
            len(delivered[delivered["delay_days"] == 0]) /
            max(len(delivered), 1) * 100, 1
        ),
    }

    return stats, df, delayed, held, lost, in_transit, pod_pend

def get_zone_shipment_summary():
    # ── reads from zone_summary materialized view ──
    query = """
        SELECT
            zone_id,
            city,
            total_shipments,
            delayed_shipments   AS delayed,
            pod_pending         AS pod_pending,
            avg_delay_days
        FROM zone_summary
        ORDER BY delayed_shipments DESC
    """
    df = pd.read_sql(query, get_engine())
    return df

def get_customer_impact():
    # ── customer level detail — stays on raw table ──
    # not aggregated in any materialized view
    query = """
        SELECT
            s.customer,
            COUNT(*) as total_shipments,
            SUM(CASE WHEN s.status='Delayed'          THEN 1 ELSE 0 END) as delayed,
            SUM(CASE WHEN s.status='Lost in Transit'  THEN 1 ELSE 0 END) as lost,
            ROUND(SUM(s.value_usd)::numeric, 0)                          as total_value,
            ROUND(AVG(s.delay_days)::numeric, 1)                         as avg_delay_days
        FROM shipments s
        WHERE s.status IN ('Delayed','Held at Hub','Lost in Transit')
        GROUP BY s.customer
        ORDER BY delayed DESC, lost DESC
        LIMIT 10
    """
    df = pd.read_sql(query, get_engine())
    return df