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
    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        where  = f"WHERE i.zone_id IN ({placeholders})"
        params = zone_ids
    else:
        where  = ""
        params = []

    query = f"""
        SELECT
            i.sku_id, i.zone_id, i.product_name, i.category,
            i.current_stock, i.reorder_point, i.avg_daily_demand,
            i.lead_time_days, i.supplier, i.unit_cost_usd,
            i.days_of_stock, i.reorder_qty, i.status,
            i.action_required, i.last_updated,
            z.zone_name, z.city, z.region, z.manager_name
        FROM inventory i
        JOIN zones z ON i.zone_id = z.zone_id
        {where}
        ORDER BY i.days_of_stock ASC
    """

    conn = get_connection()
    df   = pd.read_sql(query, conn, params=params if params else None)
    conn.close()
    return df

def get_atp(zone_ids=None):
    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        where  = f"WHERE i.zone_id IN ({placeholders})"
        params = zone_ids
    else:
        where  = ""
        params = []

    query = f"""
        SELECT
            i.sku_id, i.zone_id, i.product_name, i.category,
            i.current_stock, i.avg_daily_demand, i.reorder_point,
            i.lead_time_days, i.supplier, i.status,
            z.city,
            COALESCE(f.forecasted_demand, i.avg_daily_demand) as forecasted_demand,
            COALESCE(f.upper_bound, i.avg_daily_demand * 1.2) as upper_bound,
            COALESCE(f.lower_bound, i.avg_daily_demand * 0.8) as lower_bound
        FROM inventory i
        JOIN zones z ON i.zone_id = z.zone_id
        LEFT JOIN forecasts f ON i.sku_id  = f.sku_id
                              AND i.zone_id = f.zone_id
        {where}
        ORDER BY i.days_of_stock ASC
    """

    conn = get_connection()
    df   = pd.read_sql(query, conn, params=params if params else None)
    conn.close()

    # Calculate ATP for weeks 1 2 3 using forecasted demand
    weekly_demand         = df["forecasted_demand"] * 7
    df["atp_week1"]       = (df["current_stock"] - weekly_demand).round(0)
    df["atp_week2"]       = (df["atp_week1"] - weekly_demand).round(0)
    df["atp_week3"]       = (df["atp_week2"] - weekly_demand).round(0)

    # Worst case using upper bound demand
    weekly_demand_high    = df["upper_bound"] * 7
    df["atp_week1_worst"] = (df["current_stock"] - weekly_demand_high).round(0)
    df["atp_week2_worst"] = (df["atp_week1_worst"] - weekly_demand_high).round(0)
    df["atp_week3_worst"] = (df["atp_week2_worst"] - weekly_demand_high).round(0)

    # Stockout prediction based on which week ATP goes negative
    def stockout_week(row):
        if row["atp_week1"] <= 0:
            return "This week"
        elif row["atp_week2"] <= 0:
            return "Week 2"
        elif row["atp_week3"] <= 0:
            return "Week 3"
        return "Beyond 3 weeks"

    df["stockout_prediction"] = df.apply(stockout_week, axis=1)

    # Weeks of cover - how many full weeks of stock remain
    df["weeks_of_cover"] = (
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
    query = """
        SELECT
            i.zone_id,
            z.city,
            COUNT(*) as total_skus,
            SUM(CASE WHEN i.status='CRITICAL' THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN i.status='WARNING'  THEN 1 ELSE 0 END) as warning,
            SUM(CASE WHEN i.status='HEALTHY'  THEN 1 ELSE 0 END) as healthy,
            ROUND(AVG(i.days_of_stock)::numeric, 1) as avg_days_of_stock
        FROM inventory i
        JOIN zones z ON i.zone_id = z.zone_id
        GROUP BY i.zone_id, z.city
        ORDER BY critical DESC
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

    # Get ATP summary
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
        "most_urgent_sku":     critical.iloc[0]["product_name"] if len(critical) > 0 else "None",
        "most_urgent_days":    critical.iloc[0]["days_of_stock"] if len(critical) > 0 else 0,
        "most_urgent_zone":    critical.iloc[0]["city"] if len(critical) > 0 else "None",
        "total_reorder_qty":   int(critical["reorder_qty"].sum()) if len(critical) > 0 else 0,
        "categories_at_risk":  critical["category"].nunique() if len(critical) > 0 else 0,
        "zones_at_risk":       critical["zone_id"].nunique() if len(critical) > 0 else 0,
        "stock_value_at_risk": round((critical["current_stock"] *
                                      critical["unit_cost_usd"]).sum(), 2) if len(critical) > 0 else 0,
        "stockout_this_week":  stockout_this_week,
        "stockout_week2":      stockout_week2,
        "stockout_week3":      stockout_week3,
    }

    return stats, critical, warning, healthy, df

if __name__ == "__main__":
    stats, critical, warning, healthy, df = get_warehouse_stats()
    print(f"Total SKUs:          {stats['total_skus']}")
    print(f"Critical:            {stats['critical_count']}")
    print(f"Warning:             {stats['warning_count']}")
    print(f"Stockout this week:  {stats['stockout_this_week']} SKUs")
    print(f"Stockout week 2:     {stats['stockout_week2']} SKUs")
    print(f"Stockout week 3:     {stats['stockout_week3']} SKUs")
    print(f"Most urgent:         {stats['most_urgent_sku']} "
          f"— {stats['most_urgent_days']} days left in {stats['most_urgent_zone']}")
    print(f"Stock value at risk: ${stats['stock_value_at_risk']:,.2f}")

    print("\nATP for critical SKUs:")
    atp = get_atp()
    print(atp[atp["status"] == "CRITICAL"][[
        "sku_id", "zone_id", "product_name", "current_stock",
        "atp_week1", "atp_week2", "atp_week3", "stockout_prediction"
    ]].head(10).to_string(index=False))

    print("\nZone summary:")
    print(get_zone_summary().to_string(index=False))