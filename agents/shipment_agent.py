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

# Configurable thresholds
DELAY_THRESHOLD_DAYS  = 2
HIGH_VALUE_THRESHOLD  = 50000

def get_shipments(zone_ids=None, status_filter=None):
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
            t.performance_score as lane_performance,
            t.mode as transport_mode,
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

    # Value at risk — delayed + held + lost
    value_at_risk = round(
        delayed["value_usd"].sum() +
        held["value_usd"].sum() +
        lost["value_usd"].sum(), 2
    )

    # Most affected customer
    most_affected = delayed["customer"].value_counts().index[0] \
        if len(delayed) > 0 else "None"

    # Most problematic carrier for delays
    most_delayed_carrier = delayed["carrier"].value_counts().index[0] \
        if len(delayed) > 0 else "None"

    stats = {
        "total_shipments":      len(df),
        "delivered":            len(delivered),
        "in_transit":           len(in_transit),
        "out_for_delivery":     len(out_del),
        "delayed":              len(delayed),
        "held_at_hub":          len(held),
        "lost_in_transit":      len(lost),
        "pod_pending":          len(pod_pend),
        "avg_delay_days":       round(delayed["delay_days"].mean(), 1) if len(delayed) > 0 else 0,
        "max_delay_days":       int(delayed["delay_days"].max()) if len(delayed) > 0 else 0,
        "value_at_risk":        value_at_risk,
        "high_value_at_risk":   len(high_value_at_risk),
        "most_affected_customer": most_affected,
        "most_delayed_carrier": most_delayed_carrier,
        "on_time_delivery_pct": round(
            len(delivered[delivered["delay_days"] == 0]) /
            max(len(delivered), 1) * 100, 1
        ),
    }

    return stats, df, delayed, held, lost, in_transit, pod_pend

def get_zone_shipment_summary():
    query = """
        SELECT
            s.zone_id,
            z.city,
            COUNT(*) as total_shipments,
            SUM(CASE WHEN s.status='Delayed'          THEN 1 ELSE 0 END) as delayed,
            SUM(CASE WHEN s.status='Held at Hub'      THEN 1 ELSE 0 END) as held,
            SUM(CASE WHEN s.status='Lost in Transit'  THEN 1 ELSE 0 END) as lost,
            SUM(CASE WHEN s.status='In Transit'       THEN 1 ELSE 0 END) as in_transit,
            SUM(CASE WHEN s.status='Delivered'        THEN 1 ELSE 0 END) as delivered,
            ROUND(AVG(s.delay_days)::numeric, 1) as avg_delay_days,
            ROUND(SUM(CASE WHEN s.status IN ('Delayed','Held at Hub','Lost in Transit')
                      THEN s.value_usd ELSE 0 END)::numeric, 0) as value_at_risk
        FROM shipments s
        JOIN zones z ON s.zone_id = z.zone_id
        GROUP BY s.zone_id, z.city
        ORDER BY delayed DESC, lost DESC
    """
    df = pd.read_sql(query, get_engine())
    return df

def get_customer_impact():
    query = """
        SELECT
            s.customer,
            COUNT(*) as total_shipments,
            SUM(CASE WHEN s.status='Delayed' THEN 1 ELSE 0 END) as delayed,
            SUM(CASE WHEN s.status='Lost in Transit' THEN 1 ELSE 0 END) as lost,
            ROUND(SUM(s.value_usd)::numeric, 0) as total_value,
            ROUND(AVG(s.delay_days)::numeric, 1) as avg_delay_days
        FROM shipments s
        WHERE s.status IN ('Delayed','Held at Hub','Lost in Transit')
        GROUP BY s.customer
        ORDER BY delayed DESC, lost DESC
        LIMIT 10
    """
    df = pd.read_sql(query, get_engine())
    return df

if __name__ == "__main__":
    stats, df, delayed, held, lost, in_transit, pod_pend = \
        get_shipment_stats()

    print(f"Total shipments:      {stats['total_shipments']}")
    print(f"In transit:           {stats['in_transit']}")
    print(f"Delivered:            {stats['delivered']}")
    print(f"Delayed:              {stats['delayed']}")
    print(f"Held at hub:          {stats['held_at_hub']}")
    print(f"Lost in transit:      {stats['lost_in_transit']}")
    print(f"POD pending:          {stats['pod_pending']}")
    print(f"Avg delay:            {stats['avg_delay_days']} days")
    print(f"Max delay:            {stats['max_delay_days']} days")
    print(f"Value at risk:        $ {stats['value_at_risk']:,.0f}")
    print(f"High value at risk:   {stats['high_value_at_risk']} shipments")
    print(f"Most affected customer: {stats['most_affected_customer']}")
    print(f"Most delayed carrier: {stats['most_delayed_carrier']}")
    print(f"On time delivery pct: {stats['on_time_delivery_pct']}%")

    print("\nZone shipment summary:")
    print(get_zone_shipment_summary().to_string(index=False))

    print("\nTop 10 most affected customers:")
    print(get_customer_impact().to_string(index=False))

    print("\nDelayed shipments:")
    print(delayed[["shipment_id","zone_id","customer","carrier",
                   "status","delay_days","value_usd"]].to_string(index=False))