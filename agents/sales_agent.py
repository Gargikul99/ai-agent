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

# Reference date
TODAY = date(2026, 4, 21)

def get_sales_velocity(zone_ids=None, days=30):
    # Average daily sales per SKU per zone over last N days
    since = TODAY - timedelta(days=days)

    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        zone_filter  = f"AND s.zone_id IN ({placeholders})"
        params       = (since, *zone_ids)
    else:
        zone_filter = ""
        params      = (since,)

    query = f"""
        SELECT
            s.zone_id,
            z.city,
            s.sku_id,
            s.product_name,
            s.category,
            COUNT(*) as total_transactions,
            SUM(s.quantity_sold) as total_units_sold,
            ROUND(AVG(s.quantity_sold)::numeric, 1) as avg_daily_units,
            ROUND(SUM(s.quantity_sold * s.price_usd)::numeric, 2) as total_revenue,
            ROUND(AVG(s.price_usd)::numeric, 2) as avg_price,
            SUM(CASE WHEN s.promotion_flag = true 
                THEN s.quantity_sold ELSE 0 END) as promo_units_sold
        FROM sales s
        JOIN zones z ON s.zone_id = z.zone_id
        WHERE s.sale_date >= %s
        {zone_filter}
        GROUP BY s.zone_id, z.city, s.sku_id, s.product_name, s.category
        ORDER BY total_units_sold DESC
    """

    df = pd.read_sql(query, get_engine(), params=params)
    return df

def get_top_skus(zone_ids=None, days=30, top_n=10):
    df = get_sales_velocity(zone_ids, days)
    return df.head(top_n)

def get_slow_moving_skus(zone_ids=None, days=30, threshold=50):
    # SKUs selling below threshold units in last N days
    df = get_sales_velocity(zone_ids, days)
    return df[df["total_units_sold"] < threshold].tail(20)

def get_sales_trend(zone_ids=None):
    # Week over week comparison — last 4 weeks
    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        zone_filter  = f"AND s.zone_id IN ({placeholders})"
        params       = tuple(zone_ids)
    else:
        zone_filter = ""
        params      = None

    query = f"""
        SELECT
            CASE
                WHEN s.sale_date >= %s THEN 'Week 1 (Latest)'
                WHEN s.sale_date >= %s THEN 'Week 2'
                WHEN s.sale_date >= %s THEN 'Week 3'
                ELSE 'Week 4'
            END as week_label,
            SUM(s.quantity_sold) as total_units,
            ROUND(SUM(s.quantity_sold * s.price_usd)::numeric, 2) as total_revenue,
            COUNT(DISTINCT s.sku_id) as unique_skus_sold
        FROM sales s
        WHERE s.sale_date >= %s
        {zone_filter}
        GROUP BY week_label
        ORDER BY MIN(s.sale_date) DESC
    """

    week1 = TODAY - timedelta(days=7)
    week2 = TODAY - timedelta(days=14)
    week3 = TODAY - timedelta(days=21)
    week4 = TODAY - timedelta(days=28)

    all_params = (week1, week2, week3, week4) + (params if params else ())
    df = pd.read_sql(query, get_engine(), params=all_params)
    return df

def get_channel_breakdown(zone_ids=None, days=30):
    since = TODAY - timedelta(days=days)

    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        zone_filter  = f"AND s.zone_id IN ({placeholders})"
        params       = (since, *zone_ids)
    else:
        zone_filter = ""
        params      = (since,)

    query = f"""
        SELECT
            s.channel,
            COUNT(*) as transactions,
            SUM(s.quantity_sold) as total_units,
            ROUND(SUM(s.quantity_sold * s.price_usd)::numeric, 2) as revenue,
            ROUND(AVG(s.quantity_sold)::numeric, 1) as avg_order_size
        FROM sales s
        WHERE s.sale_date >= %s
        {zone_filter}
        GROUP BY s.channel
        ORDER BY revenue DESC
    """

    df = pd.read_sql(query, get_engine(), params=params)
    return df

def get_category_performance(zone_ids=None, days=30):
    since = TODAY - timedelta(days=days)

    if zone_ids and zone_ids != ["ALL"]:
        placeholders = ",".join(["%s"] * len(zone_ids))
        zone_filter  = f"AND s.zone_id IN ({placeholders})"
        params       = (since, *zone_ids)
    else:
        zone_filter = ""
        params      = (since,)

    query = f"""
        SELECT
            s.category,
            SUM(s.quantity_sold) as total_units,
            ROUND(SUM(s.quantity_sold * s.price_usd)::numeric, 2) as revenue,
            ROUND(AVG(s.quantity_sold)::numeric, 1) as avg_daily_units,
            SUM(CASE WHEN s.promotion_flag = true
                THEN s.quantity_sold ELSE 0 END) as promo_units,
            ROUND(
                SUM(CASE WHEN s.promotion_flag = true
                    THEN s.quantity_sold ELSE 0 END)::numeric /
                NULLIF(SUM(s.quantity_sold), 0) * 100, 1
            ) as promo_pct
        FROM sales s
        WHERE s.sale_date >= %s
        {zone_filter}
        GROUP BY s.category
        ORDER BY revenue DESC
    """

    df = pd.read_sql(query, get_engine(), params=params)
    return df

def get_sales_stats(zone_ids=None):
    velocity = get_sales_velocity(zone_ids, days=30)
    trend    = get_sales_trend(zone_ids)
    channel  = get_channel_breakdown(zone_ids)
    category = get_category_performance(zone_ids)

    # Week over week change
    if len(trend) >= 2:
        latest_units  = trend.iloc[0]["total_units"]
        previous_units= trend.iloc[1]["total_units"]
        wow_change    = round((latest_units - previous_units) /
                              max(previous_units, 1) * 100, 1)
    else:
        wow_change = 0

    stats = {
        "total_units_30d":    int(velocity["total_units_sold"].sum()),
        "total_revenue_30d":  round(velocity["total_revenue"].sum(), 2),
        "top_sku":            velocity.iloc[0]["product_name"] if len(velocity) > 0 else "None",
        "top_sku_units":      int(velocity.iloc[0]["total_units_sold"]) if len(velocity) > 0 else 0,
        "top_category":       category.iloc[0]["category"] if len(category) > 0 else "None",
        "top_channel":        channel.iloc[0]["channel"] if len(channel) > 0 else "None",
        "wow_change_pct":     wow_change,
        "slow_moving_count":  len(get_slow_moving_skus(zone_ids)),
        "unique_skus_sold":   velocity["sku_id"].nunique(),
    }

    return stats, velocity, trend, channel, category

if __name__ == "__main__":
    stats, velocity, trend, channel, category = get_sales_stats()

    print(f"Total units sold (30d):  {stats['total_units_30d']:,}")
    print(f"Total revenue (30d):     ${stats['total_revenue_30d']:,.2f}")
    print(f"Top selling SKU:         {stats['top_sku']} ({stats['top_sku_units']:,} units)")
    print(f"Top category:            {stats['top_category']}")
    print(f"Top channel:             {stats['top_channel']}")
    print(f"Week over week change:   {stats['wow_change_pct']}%")
    print(f"Slow moving SKUs:        {stats['slow_moving_count']}")

    print("\nSales trend (last 4 weeks):")
    print(trend.to_string(index=False))

    print("\nChannel breakdown:")
    print(channel.to_string(index=False))

    print("\nCategory performance:")
    print(category.to_string(index=False))

    print("\nTop 10 SKUs by volume:")
    print(get_top_skus().to_string(index=False))