import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_inventory(zone_ids=None):
    # ── reads from inventory_summary materialized view ──
    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        where  = f"WHERE zone_id IN ({placeholders})"
        params = zone_ids
    else:
        where  = ""
        params = []

    query = f"""
        SELECT
            sku_id, zone_id, product_name, category,
            current_stock, reorder_point, avg_daily_demand,
            lead_time_days, supplier, unit_cost_usd,
            days_of_stock, reorder_qty, status,
            action_required, last_updated,
            zone_name, city, region
        FROM inventory_summary
        {where}
        ORDER BY days_of_stock ASC
    """

    conn = get_connection()
    df   = pd.read_sql(query, conn, params=params if params else None)
    conn.close()
    return df

def get_atp(zone_ids=None):
    # ── reads from inventory_summary — forecast already joined ──
    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        where  = f"WHERE zone_id IN ({placeholders})"
        params = zone_ids
    else:
        where  = ""
        params = []

    query = f"""
        SELECT
            sku_id, zone_id, product_name, category,
            current_stock, avg_daily_demand, reorder_point,
            lead_time_days, supplier, status, city,
            COALESCE(forecasted_demand, avg_daily_demand)       AS forecasted_demand,
            COALESCE(upper_bound, avg_daily_demand * 1.2)       AS upper_bound,
            COALESCE(lower_bound, avg_daily_demand * 0.8)       AS lower_bound
        FROM inventory_summary
        {where}
        ORDER BY days_of_stock ASC
    """

    conn = get_connection()
    df   = pd.read_sql(query, conn, params=params if params else None)
    conn.close()

    # ATP calculations — unchanged
    weekly_demand         = df["forecasted_demand"] * 7
    df["atp_week1"]       = (df["current_stock"] - weekly_demand).round(0)
    df["atp_week2"]       = (df["atp_week1"] - weekly_demand).round(0)
    df["atp_week3"]       = (df["atp_week2"] - weekly_demand).round(0)

    weekly_demand_high    = df["upper_bound"] * 7
    df["atp_week1_worst"] = (df["current_stock"] - weekly_demand_high).round(0)
    df["atp_week2_worst"] = (df["atp_week1_worst"] - weekly_demand_high).round(0)
    df["atp_week3_worst"] = (df["atp_week2_worst"] - weekly_demand_high).round(0)

    def stockout_week(row):
        if row["atp_week1"] <= 0:   return "This week"
        elif row["atp_week2"] <= 0: return "Week 2"
        elif row["atp_week3"] <= 0: return "Week 3"
        return "Beyond 3 weeks"

    df["stockout_prediction"] = df.apply(stockout_week, axis=1)
    df["weeks_of_cover"]      = (
        df["current_stock"] / (df["forecasted_demand"] * 7)
    ).round(1)

    return df[[
        "sku_id", "zone_id", "product_name", "category", "city",
        "current_stock", "forecasted_demand", "status",
        "atp_week1", "atp_week2", "atp_week3",
        "atp_week1_worst", "atp_week2_worst", "atp_week3_worst",
        "weeks_of_cover", "stockout_prediction",
        "lead_time_days", "supplier"
    ]]

def get_zone_summary():
    # ── reads from zone_summary materialized view ──
    query = """
        SELECT
            zone_id, city,
            total_skus,
            critical_skus   AS critical,
            warning_skus    AS warning,
            healthy_skus    AS healthy,
            avg_days_of_stock
        FROM zone_summary
        ORDER BY critical_skus DESC
    """
    conn = get_connection()
    df   = pd.read_sql(query, conn)
    conn.close()
    return df

def get_warehouse_stats(zone_ids=None):
    df       = get_inventory(zone_ids)
    critical = df[df["status"] == "CRITICAL"]
    warning  = df[df["status"] == "WARNING"]
    healthy  = df[df["status"] == "HEALTHY"]

    atp_df             = get_atp(zone_ids)
    stockout_this_week = len(atp_df[atp_df["stockout_prediction"] == "This week"])
    stockout_week2     = len(atp_df[atp_df["stockout_prediction"] == "Week 2"])
    stockout_week3     = len(atp_df[atp_df["stockout_prediction"] == "Week 3"])

    stats = {
        "total_skus":          len(df),
        "critical_count":      len(critical),
        "warning_count":       len(warning),
        "healthy_count":       len(healthy),
        "critical_pct":        round(len(critical) / len(df) * 100, 1) if len(df) > 0 else 0,
        "most_urgent_sku":     critical.iloc[0]["product_name"]  if len(critical) > 0 else "None",
        "most_urgent_days":    critical.iloc[0]["days_of_stock"] if len(critical) > 0 else 0,
        "most_urgent_zone":    critical.iloc[0]["city"]          if len(critical) > 0 else "None",
        "total_reorder_qty":   int(critical["reorder_qty"].sum()) if len(critical) > 0 else 0,
        "categories_at_risk":  critical["category"].nunique()    if len(critical) > 0 else 0,
        "zones_at_risk":       critical["zone_id"].nunique()     if len(critical) > 0 else 0,
        "stock_value_at_risk": round((critical["current_stock"] *
                                      critical["unit_cost_usd"]).sum(), 2) if len(critical) > 0 else 0,
        "stockout_this_week":  stockout_this_week,
        "stockout_week2":      stockout_week2,
        "stockout_week3":      stockout_week3,
    }

    return stats, critical, warning, healthy, df