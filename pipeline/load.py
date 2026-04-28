import psycopg2
import os
import uuid
import time
from datetime import datetime
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

def log_pipeline_run(conn, cur, table_name, trigger_source,
                     rows_inserted, rows_updated,
                     status, duration, error=None):
    cur.execute("""
        INSERT INTO pipeline_log VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        str(uuid.uuid4()),
        datetime.now(),
        table_name,
        trigger_source,
        rows_inserted,
        rows_updated,
        status,
        round(duration, 3),
        error
    ))

def load_inventory(conn, cur, df, trigger_source="manual"):
    start = time.time()
    try:
        cur.executemany("""
            INSERT INTO inventory VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, df[['sku_id','zone_id','product_name','category',
                 'current_stock','reorder_point','avg_daily_demand',
                 'lead_time_days','supplier','unit_cost_inr',
                 'days_of_stock','reorder_qty','status',
                 'action_required','last_updated']].values.tolist())

        duration = time.time() - start
        log_pipeline_run(conn, cur, 'inventory', trigger_source,
                         len(df), 0, 'success', duration)
        print(f"Inventory loaded: {len(df)} records in {duration:.2f}s")

    except Exception as e:
        duration = time.time() - start
        log_pipeline_run(conn, cur, 'inventory', trigger_source,
                         0, 0, 'error', duration, str(e))
        print(f"Inventory load failed: {e}")
        raise

def load_transport(conn, cur, df, trigger_source="manual"):
    start = time.time()
    try:
        cur.executemany("""
            INSERT INTO transport VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, df[['lane_id','zone_id','origin','destination',
                 'carrier','mode','distance_km',
                 'planned_transit_days','actual_transit_days',
                 'on_time','delay_days','cost_per_kg_inr',
                 'damage_rate_pct','performance_score',
                 'last_updated']].values.tolist())

        duration = time.time() - start
        log_pipeline_run(conn, cur, 'transport', trigger_source,
                         len(df), 0, 'success', duration)
        print(f"Transport loaded: {len(df)} records in {duration:.2f}s")

    except Exception as e:
        duration = time.time() - start
        log_pipeline_run(conn, cur, 'transport', trigger_source,
                         0, 0, 'error', duration, str(e))
        print(f"Transport load failed: {e}")
        raise

def load_shipments(conn, cur, df, trigger_source="manual"):
    start = time.time()
    try:
        cur.executemany("""
            INSERT INTO shipments VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, df[['shipment_id','order_id','zone_id','lane_id',
                 'origin','customer','category','carrier',
                 'status','dispatch_date','planned_delivery',
                 'actual_delivery','delay_days','weight_kg',
                 'value_inr','pod_received',
                 'last_updated']].values.tolist())

        duration = time.time() - start
        log_pipeline_run(conn, cur, 'shipments', trigger_source,
                         len(df), 0, 'success', duration)
        print(f"Shipments loaded: {len(df)} records in {duration:.2f}s")

    except Exception as e:
        duration = time.time() - start
        log_pipeline_run(conn, cur, 'shipments', trigger_source,
                         0, 0, 'error', duration, str(e))
        print(f"Shipments load failed: {e}")
        raise

def load_all(inv, trn, shp, sal, fct, trigger_source="manual"):
    conn = get_connection()
    cur  = conn.cursor()
    print(f"Load starting at {datetime.now().strftime('%H:%M:%S')}")

    # Delete in correct order - children before parents
    cur.execute("DELETE FROM forecasts")
    cur.execute("DELETE FROM sales")
    cur.execute("DELETE FROM shipments")
    cur.execute("DELETE FROM transport")
    cur.execute("DELETE FROM inventory")
    print("Existing data cleared")

    load_inventory(conn, cur, inv, trigger_source)
    load_transport(conn, cur, trn, trigger_source)
    load_shipments(conn, cur, shp, trigger_source)
    load_sales(conn, cur, sal, trigger_source)
    load_forecasts(conn, cur, fct, trigger_source)


    conn.commit()
    cur.close()
    conn.close()
    print(f"Load complete at {datetime.now().strftime('%H:%M:%S')}")

def load_sales(conn, cur, df, trigger_source="manual"):
    start = time.time()
    try:
        cur.executemany("""
            INSERT INTO sales VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, df[['sale_id','zone_id','sku_id','product_name',
                 'category','quantity_sold','sale_date',
                 'customer','channel','price_inr',
                 'promotion_flag','last_updated']].values.tolist())

        duration = time.time() - start
        log_pipeline_run(conn, cur, 'sales', trigger_source,
                         len(df), 0, 'success', duration)
        print(f"Sales loaded: {len(df):,} records in {duration:.2f}s")

    except Exception as e:
        duration = time.time() - start
        log_pipeline_run(conn, cur, 'sales', trigger_source,
                         0, 0, 'error', duration, str(e))
        print(f"Sales load failed: {e}")
        raise

def load_forecasts(conn, cur, df, trigger_source="manual"):
    start = time.time()
    try:
        cur.executemany("""
            INSERT INTO forecasts VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, df[['forecast_id','zone_id','sku_id','forecast_date',
                 'forecasted_demand','rolling_avg_30d',
                 'upper_bound','lower_bound',
                 'generated_at']].values.tolist())

        duration = time.time() - start
        log_pipeline_run(conn, cur, 'forecasts', trigger_source,
                         len(df), 0, 'success', duration)
        print(f"Forecasts loaded: {len(df)} records in {duration:.2f}s")

    except Exception as e:
        duration = time.time() - start
        log_pipeline_run(conn, cur, 'forecasts', trigger_source,
                         0, 0, 'error', duration, str(e))
        print(f"Forecasts load failed: {e}")
        raise

if __name__ == "__main__":
    from extract import extract_all
    from transform import transform_all

    inventory, transport, shipments, sales, forecasts = extract_all()
    inv, trn, shp, sal, fct = transform_all(
        inventory, transport, shipments, sales, forecasts)
    load_all(inv, trn, shp, sal, fct)