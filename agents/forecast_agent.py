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
    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        where  = f"AND f.zone_id IN ({placeholders})"
        params = tuple(zone_ids)
    else:
        where  = ""
        params = None

    query = f"""
        SELECT
            f.forecast_id, f.zone_id, f.sku_id,
            f.forecasted_demand, f.rolling_avg_30d,
            f.upper_bound, f.lower_bound, f.generated_at,
            i.product_name, i.category, i.current_stock,
            i.avg_daily_demand, i.reorder_point,
            i.lead_time_days, i.supplier, i.status,
            z.city, z.region
        FROM forecasts f
        JOIN inventory i ON f.sku_id  = i.sku_id
                        AND f.zone_id = i.zone_id
        JOIN zones z ON f.zone_id = z.zone_id
        WHERE 1=1
        {where}
        ORDER BY f.forecasted_demand DESC
    """

    df = pd.read_sql(query, get_engine(), params=params)
    return df

def get_two_week_forecast(zone_ids=None):
    df = get_forecasts(zone_ids)

    # Calculate 2 week demand forecast
    df["forecast_week1"]  = (df["forecasted_demand"] * 7).round(0)
    df["forecast_week2"]  = (df["forecasted_demand"] * 7).round(0)
    df["forecast_2weeks"] = (df["forecasted_demand"] * 14).round(0)

    # Worst case scenario using upper bound
    df["forecast_2weeks_worst"] = (df["upper_bound"] * 14).round(0)

    # Best case scenario using lower bound
    df["forecast_2weeks_best"]  = (df["lower_bound"] * 14).round(0)

    # Stock coverage check
    df["stock_covers_2weeks"] = df["current_stock"] >= df["forecast_2weeks"]
    df["stock_gap"]           = (df["current_stock"] - df["forecast_2weeks"]).round(0)

    # Confidence band width — wider = less reliable forecast
    df["confidence_band"] = (df["upper_bound"] - df["lower_bound"]).round(1)
    df["high_uncertainty"] = df["confidence_band"] > df["forecasted_demand"] * 0.5

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
    # SKUs where current stock won't cover 2 week forecast
    at_risk = df[df["stock_covers_2weeks"] == False].sort_values("stock_gap")
    return at_risk

def get_forecast_accuracy(zone_ids=None):
    # Compare rolling avg forecast against actual sales
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
            ROUND(AVG(s.quantity_sold)::numeric, 1) as actual_avg_daily,
            f.rolling_avg_30d as forecasted_avg_daily,
            ROUND(ABS(AVG(s.quantity_sold) - f.rolling_avg_30d)::numeric, 1) as abs_error,
            ROUND(
                (ABS(AVG(s.quantity_sold) - f.rolling_avg_30d) /
                NULLIF(AVG(s.quantity_sold), 0) * 100)::numeric, 1
                ) as mape
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

    since  = TODAY - timedelta(days=30)
    all_params = (since,) + (params if params else ())
    df = pd.read_sql(query, get_engine(), params=all_params)
    return df

def get_zone_demand_outlook(zone_ids=None):
    df = get_two_week_forecast(zone_ids)

    zone_outlook = df.groupby(["zone_id","city"]).agg(
        total_2week_demand    =("forecast_2weeks",      "sum"),
        total_2week_worst     =("forecast_2weeks_worst","sum"),
        skus_at_risk          =("stock_covers_2weeks",  lambda x: (~x).sum()),
        high_uncertainty_skus =("high_uncertainty",     "sum"),
        avg_stock_gap         =("stock_gap",            "mean"),
    ).round(1).reset_index().sort_values("skus_at_risk", ascending=False)

    return zone_outlook

def get_forecast_stats(zone_ids=None):
    df       = get_two_week_forecast(zone_ids)
    at_risk  = get_stockout_risk(zone_ids)
    accuracy = get_forecast_accuracy(zone_ids)

    stats = {
        "total_skus_forecasted":   len(df),
        "skus_at_risk_2weeks":     len(at_risk),
        "skus_covered_2weeks":     len(df[df["stock_covers_2weeks"] == True]),
        "high_uncertainty_skus":   int(df["high_uncertainty"].sum()),
        "total_2week_demand":      int(df["forecast_2weeks"].sum()),
        "total_2week_worst_case":  int(df["forecast_2weeks_worst"].sum()),
        "avg_mape":                round(accuracy["mape"].mean(), 1) if len(accuracy) > 0 else 0,
        "most_at_risk_sku":        at_risk.iloc[0]["product_name"] if len(at_risk) > 0 else "None",
        "most_at_risk_zone":       at_risk.iloc[0]["city"] if len(at_risk) > 0 else "None",
        "largest_stock_gap":       int(at_risk.iloc[0]["stock_gap"]) if len(at_risk) > 0 else 0,
    }

    return stats, df, at_risk

if __name__ == "__main__":
    stats, df, at_risk = get_forecast_stats()

    print(f"Total SKUs forecasted:    {stats['total_skus_forecasted']}")
    print(f"SKUs at risk (2 weeks):   {stats['skus_at_risk_2weeks']}")
    print(f"SKUs covered (2 weeks):   {stats['skus_covered_2weeks']}")
    print(f"High uncertainty SKUs:    {stats['high_uncertainty_skus']}")
    print(f"Total 2-week demand:      {stats['total_2week_demand']:,} units")
    print(f"Worst case 2-week demand: {stats['total_2week_worst_case']:,} units")
    print(f"Avg forecast error (MAPE):{stats['avg_mape']}%")
    print(f"Most at risk SKU:         {stats['most_at_risk_sku']} "
          f"in {stats['most_at_risk_zone']}")
    print(f"Largest stock gap:        {stats['largest_stock_gap']:,} units")

    print("\nZone demand outlook (2 weeks):")
    print(get_zone_demand_outlook().to_string(index=False))

    print("\nTop 10 SKUs at stockout risk:")
    print(at_risk[[
        "sku_id", "zone_id", "product_name", "current_stock",
        "forecast_2weeks", "stock_gap", "supplier"
    ]].head(10).to_string(index=False))

    print("\nForecast accuracy (top 10 worst MAPE):")
    print(get_forecast_accuracy().head(10).to_string(index=False))