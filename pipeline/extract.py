import psycopg2
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_engine():
    return create_engine(
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )


def extract_all():
    conn = get_engine()
    print(f"Extract starting at {datetime.now().strftime('%H:%M:%S')}")

    # Pull inventory with zone details joined in
    inventory = pd.read_sql("""
        SELECT i.*, z.zone_name, z.city, z.region,
               z.warehouse_address, z.capacity_sqft, z.manager_name
        FROM inventory i
        JOIN zones z ON i.zone_id = z.zone_id
    """, conn)
    print(f"Inventory: {len(inventory)} records")

    # Basic null check on critical columns
    nulls = inventory[['sku_id','zone_id','current_stock',
                        'avg_daily_demand']].isnull().sum()
    if nulls.any():
        print(f"Warning - nulls found: {nulls[nulls>0].to_dict()}")
    else:
        print("Inventory validation passed")

    # Pull transport lanes with zone details
    transport = pd.read_sql("""
        SELECT t.*, z.city, z.region
        FROM transport t
        JOIN zones z ON t.zone_id = z.zone_id
    """, conn)
    print(f"Transport: {len(transport)} records")

    # Pull shipments joined to zones and transport lanes
    # LEFT JOIN on transport because some shipments may not
    # have a matching lane if data is incomplete
    shipments = pd.read_sql("""
        SELECT s.*, z.city, z.region,
               t.carrier as lane_carrier,
               t.mode as transport_mode,
               t.distance_km,
               t.performance_score as lane_performance
        FROM shipments s
        JOIN zones z ON s.zone_id = z.zone_id
        LEFT JOIN transport t ON s.lane_id = t.lane_id
    """, conn)
    print(f"Shipments: {len(shipments)} records")

    # Pull sales history with zone details
    sales = pd.read_sql("""
        SELECT s.*, z.city, z.region
        FROM sales s
        JOIN zones z ON s.zone_id = z.zone_id
    """, conn)
    print(f"Sales: {len(sales):,} records")

    # Pull forecasts joined to inventory for product context
    forecasts = pd.read_sql("""
        SELECT f.*, i.product_name, i.category,
               i.current_stock, i.avg_daily_demand,
               i.status as inventory_status
        FROM forecasts f
        JOIN inventory i ON f.sku_id  = i.sku_id
                        AND f.zone_id = i.zone_id
    """, conn)
    print(f"Forecasts: {len(forecasts)} records")

    conn.dispose()
    print(f"Extract complete at {datetime.now().strftime('%H:%M:%S')}")

    return inventory, transport, shipments, sales, forecasts

if __name__ == "__main__":
    inventory, transport, shipments, sales, forecasts = extract_all()
    print("\nSample inventory row:")
    print(inventory.head(1).T)