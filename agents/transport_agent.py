import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

# Configurable thresholds
COST_THRESHOLD_PER_KG    = 5.0   # flag lanes above this cost per kg
DELAY_THRESHOLD_DAYS     = 2     # flag lanes with avg delay above this
PERFORMANCE_THRESHOLD    = 65.0  # flag carriers below this score

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_engine():
    return create_engine(
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )

def get_transport(zone_ids=None):
    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        where  = f"WHERE t.zone_id IN ({placeholders})"
        params = zone_ids
    else:
        where  = ""
        params = []

    query = f"""
        SELECT
            t.lane_id, t.zone_id, t.origin, t.destination,
            t.carrier, t.mode, t.distance_km,
            t.planned_transit_days, t.actual_transit_days,
            t.on_time, t.delay_days, t.cost_per_kg_usd,
            t.damage_rate_pct, t.performance_score,
            t.last_updated,
            z.city, z.region
        FROM transport t
        JOIN zones z ON t.zone_id = z.zone_id
        {where}
        ORDER BY t.performance_score ASC
    """

    df = pd.read_sql(query, get_engine(),
                     params=params if params else None)
    return df

def get_transport_stats(zone_ids=None):
    df = get_transport(zone_ids)

    # Apply thresholds
    delayed     = df[df["delay_days"] > DELAY_THRESHOLD_DAYS]
    expensive   = df[df["cost_per_kg_usd"] > COST_THRESHOLD_PER_KG]
    poor        = df[df["performance_score"] < PERFORMANCE_THRESHOLD]
    on_time     = df[df["on_time"] == True]

    # Carrier level summary
    carrier_summary = df.groupby("carrier").agg(
        total_lanes     =("lane_id",          "count"),
        on_time_pct     =("on_time",          lambda x: round(x.mean() * 100, 1)),
        avg_delay_days  =("delay_days",       "mean"),
        avg_cost_per_kg =("cost_per_kg_usd",  "mean"),
        avg_damage_rate =("damage_rate_pct",  "mean"),
        avg_perf_score  =("performance_score","mean"),
    ).round(2).reset_index().sort_values("avg_perf_score")

    # Route optimization — best carrier per zone
    best_per_zone = df.sort_values("performance_score", ascending=False)\
                  .groupby("zone_id")\
                  .first()\
                  .reset_index()[["zone_id","city","carrier",
                                  "performance_score","cost_per_kg_usd"]]

    stats = {
        "total_lanes":        len(df),
        "on_time_lanes":      len(on_time),
        "delayed_lanes":      len(delayed),
        "on_time_pct":        round(len(on_time) / len(df) * 100, 1) if len(df) > 0 else 0,
        "avg_delay_days":     round(df["delay_days"].mean(), 1),
        "poor_performers":    len(poor),
        "expensive_lanes":    len(expensive),
        "avg_cost_per_kg":    round(df["cost_per_kg_usd"].mean(), 2),
        "avg_damage_rate":    round(df["damage_rate_pct"].mean(), 2),
        "worst_carrier":      carrier_summary.iloc[0]["carrier"] if len(carrier_summary) > 0 else "None",
        "best_carrier":       carrier_summary.iloc[-1]["carrier"] if len(carrier_summary) > 0 else "None",
        "worst_carrier_score":round(carrier_summary.iloc[0]["avg_perf_score"], 1) if len(carrier_summary) > 0 else 0,
        "best_carrier_score": round(carrier_summary.iloc[-1]["avg_perf_score"], 1) if len(carrier_summary) > 0 else 0,
        "total_zones":        df["zone_id"].nunique(),
    }

    return stats, df, delayed, expensive, poor, carrier_summary, best_per_zone

def get_route_optimizer(origin_zone, destination=None):
    # Find best route from a zone optionally filtered by destination
    query = """
        SELECT
            t.lane_id, t.zone_id, t.origin, t.destination,
            t.carrier, t.mode, t.distance_km,
            t.planned_transit_days, t.actual_transit_days,
            t.on_time, t.delay_days, t.cost_per_kg_usd,
            t.damage_rate_pct, t.performance_score,
            z.city
        FROM transport t
        JOIN zones z ON t.zone_id = z.zone_id
        WHERE t.zone_id = %s
        ORDER BY t.performance_score DESC
    """
    df = pd.read_sql(query, get_engine(), params=(origin_zone,))

    if destination:
        df = df[df["destination"].str.contains(destination, case=False)]

    if len(df) == 0:
        return None

    best = df.iloc[0]
    return {
        "recommended_carrier":  best["carrier"],
        "lane_id":              best["lane_id"],
        "origin":               best["origin"],
        "destination":          best["destination"],
        "mode":                 best["mode"],
        "distance_km":          best["distance_km"],
        "planned_transit_days": best["planned_transit_days"],
        "cost_per_kg_usd":      best["cost_per_kg_usd"],
        "performance_score":    best["performance_score"],
        "on_time_rate":         f"{round(df['on_time'].mean() * 100, 1)}%",
        "alternatives":         df[["carrier","performance_score",
                                    "cost_per_kg_usd","planned_transit_days"]].head(3)
    }

def get_zone_transport_summary():
    query = """
        SELECT
            t.zone_id,
            z.city,
            COUNT(*) as total_lanes,
            SUM(CASE WHEN t.on_time = true THEN 1 ELSE 0 END) as on_time_lanes,
            ROUND(AVG(t.performance_score)::numeric, 1) as avg_perf_score,
            ROUND(AVG(t.cost_per_kg_usd)::numeric, 2) as avg_cost_per_kg,
            ROUND(AVG(t.delay_days)::numeric, 1) as avg_delay_days,
            SUM(CASE WHEN t.delay_days > %s THEN 1 ELSE 0 END) as lanes_above_delay_threshold,
            SUM(CASE WHEN t.cost_per_kg_usd > %s THEN 1 ELSE 0 END) as lanes_above_cost_threshold
        FROM transport t
        JOIN zones z ON t.zone_id = z.zone_id
        GROUP BY t.zone_id, z.city
        ORDER BY avg_perf_score ASC
    """
    df = pd.read_sql(query, get_engine(),
                     params=(DELAY_THRESHOLD_DAYS, COST_THRESHOLD_PER_KG
                     ))
    return df

if __name__ == "__main__":
    stats, df, delayed, expensive, poor, carrier_summary, best_per_zone = \
        get_transport_stats()

    print(f"Total lanes:       {stats['total_lanes']}")
    print(f"On time:           {stats['on_time_pct']}%")
    print(f"Delayed lanes:     {stats['delayed_lanes']} "
          f"(above {DELAY_THRESHOLD_DAYS} day threshold)")
    print(f"Expensive lanes:   {stats['expensive_lanes']} "
          f"(above USD {COST_THRESHOLD_PER_KG}/kg)")
    print(f"Poor performers:   {stats['poor_performers']} "
          f"(below score {PERFORMANCE_THRESHOLD})")
    print(f"Best carrier:      {stats['best_carrier']} "
          f"(score {stats['best_carrier_score']})")
    print(f"Worst carrier:     {stats['worst_carrier']} "
          f"(score {stats['worst_carrier_score']})")

    print("\nCarrier summary:")
    print(carrier_summary.to_string(index=False))

    print("\nZone transport summary:")
    print(get_zone_transport_summary().to_string(index=False))

    print("\nRoute optimizer — Zone A (Los Angeles):")
    result = get_route_optimizer("A")
    if result:
        print(f"  Recommended: {result['recommended_carrier']}")
        print(f"  Route:       {result['origin']} → {result['destination']}")
        print(f"  Transit:     {result['planned_transit_days']} days")
        print(f"  Cost:        USD {result['cost_per_kg_usd']}/kg")
        print(f"  Score:       {result['performance_score']}")
        print(f"\n  Alternatives:")
        print(result["alternatives"].to_string(index=False))