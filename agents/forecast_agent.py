import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from datetime import date, timedelta

load_dotenv()

def get_engine():
    return create_engine(
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )

TODAY = date(2026, 4, 21)

def get_forecasts(zone_ids=None):
    # ── reads from inventory_summary materialized view ──
    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        where  = f"WHERE zone_id IN ({placeholders})"
        params = tuple(zone_ids)
    else:
        where  = ""
        params = None

    query = f"""
        SELECT
            sku_id, zone_id, product_name, category,
            city, region, current_stock, avg_daily_demand,
            reorder_point, lead_time_days, supplier, status,
            forecasted_demand, rolling_avg_30d,
            upper_bound, lower_bound, forecast_date
        FROM inventory_summary
        {where}
        ORDER BY forecasted_demand DESC
    """

    df = pd.read_sql(query, get_engine(), params=params)
    return df

def get_two_week_forecast(zone_ids=None):
    df = get_forecasts(zone_ids)

    df["forecast_week1"]        = (df["forecasted_demand"] * 7).round(0)
    df["forecast_week2"]        = (df["forecasted_demand"] * 7).round(0)
    df["forecast_2weeks"]       = (df["forecasted_demand"] * 14).round(0)
    df["forecast_2weeks_worst"] = (df["upper_bound"] * 14).round(0)
    df["forecast_2weeks_best"]  = (df["lower_bound"] * 14).round(0)
    df["stock_covers_2weeks"]   = df["current_stock"] >= df["forecast_2weeks"]
    df["stock_gap"]             = (df["current_stock"] - df["forecast_2weeks"]).round(0)
    df["confidence_band"]       = (df["upper_bound"] - df["lower_bound"]).round(1)
    df["high_uncertainty"]      = df["confidence_band"] > df["forecasted_demand"] * 0.5

    return df[[
        "sku_id", "zone_id", "product_name", "category", "city",
        "current_stock", "forecasted_demand", "status",
        "forecast_week1", "forecast_week2", "forecast_2weeks",
        "forecast_2weeks_worst", "forecast_2weeks_best",
        "stock_covers_2weeks", "stock_gap",
        "confidence_band", "high_uncertainty",
        "lead_time_days", "supplier", "reorder_point"
    ]]

def get_stockout_risk(zone_ids=None):
    df = get_two_week_forecast(zone_ids)
    at_risk = df[df["stock_covers_2weeks"] == False].sort_values("stock_gap")
    return at_risk

def get_forecast_accuracy(zone_ids=None):
    # ── reads from raw tables — needs sales join, cannot use view ──
    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        zone_filter  = f"AND s.zone_id IN ({placeholders})"
        params       = tuple(zone_ids)
    else:
        zone_filter = ""
        params      = None

    query = f"""
        SELECT
            s.zone_id,
            z.city,
            s.sku_id,
            s.product_name,
            ROUND(AVG(s.quantity_sold)::numeric, 1)       AS actual_avg_daily,
            f.rolling_avg_30d                              AS forecasted_avg_daily,
            ROUND(ABS(AVG(s.quantity_sold) 
                  - f.rolling_avg_30d)::numeric, 1)       AS abs_error,
            ROUND(
                (ABS(AVG(s.quantity_sold) - f.rolling_avg_30d) /
                NULLIF(AVG(s.quantity_sold), 0) * 100
                )::numeric, 1)                             AS mape
        FROM sales s
        JOIN zones z ON s.zone_id = z.zone_id
        JOIN forecasts f ON s.sku_id  = f.sku_id
                        AND s.zone_id = f.zone_id
        WHERE s.sale_date >= %s
        {zone_filter}
        GROUP BY s.zone_id, z.city, s.sku_id,
                 s.product_name, f.rolling_avg_30d
        ORDER BY mape DESC
    """

    since     = TODAY - timedelta(days=30)
    all_params = (since,) + (params if params else ())
    df = pd.read_sql(query, get_engine(), params=all_params)
    return df

def get_zone_demand_outlook(zone_ids=None):
    df = get_two_week_forecast(zone_ids)

    zone_outlook = df.groupby(["zone_id","city"]).agg(
        total_2week_demand    =("forecast_2weeks",       "sum"),
        total_2week_worst     =("forecast_2weeks_worst", "sum"),
        skus_at_risk          =("stock_covers_2weeks",   lambda x: (~x).sum()),
        high_uncertainty_skus =("high_uncertainty",      "sum"),
        avg_stock_gap         =("stock_gap",             "mean"),
    ).round(1).reset_index().sort_values("skus_at_risk", ascending=False)

    return zone_outlook

def get_forecast_stats(zone_ids=None):
    df       = get_two_week_forecast(zone_ids)
    at_risk  = get_stockout_risk(zone_ids)
    accuracy = get_forecast_accuracy(zone_ids)

    stats = {
        "total_skus_forecasted":  len(df),
        "skus_at_risk_2weeks":    len(at_risk),
        "skus_covered_2weeks":    len(df[df["stock_covers_2weeks"] == True]),
        "high_uncertainty_skus":  int(df["high_uncertainty"].sum()),
        "total_2week_demand":     int(df["forecast_2weeks"].sum()),
        "total_2week_worst_case": int(df["forecast_2weeks_worst"].sum()),
        "avg_mape":               round(accuracy["mape"].mean(), 1) if len(accuracy) > 0 else 0,
        "most_at_risk_sku":       at_risk.iloc[0]["product_name"] if len(at_risk) > 0 else "None",
        "most_at_risk_zone":      at_risk.iloc[0]["city"]         if len(at_risk) > 0 else "None",
        "largest_stock_gap":      int(at_risk.iloc[0]["stock_gap"]) if len(at_risk) > 0 else 0,
    }

    return stats, df, at_risk