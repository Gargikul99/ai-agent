import duckdb
import os
import uuid
import time
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__),
                       "../database/supply_chain.duckdb")

def log_pipeline_run(conn, table_name, trigger_source,
                     rows_inserted, rows_updated, 
                     status, duration, error=None):
    # Write every pipeline run to pipeline_log for audit trail
    conn.execute("""
        INSERT INTO pipeline_log VALUES (?,?,?,?,?,?,?,?,?)
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

def load_inventory(conn, df, trigger_source="manual"):
    start = time.time()
    try:
        # Delete existing records and reload clean transformed data
        conn.execute("DELETE FROM inventory")
        conn.executemany("""
            INSERT INTO inventory VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, df[['sku_id','zone_id','product_name','category',
                 'current_stock','reorder_point','avg_daily_demand',
                 'lead_time_days','supplier','unit_cost_inr',
                 'days_of_stock','reorder_qty','status',
                 'action_required','last_updated']].values.tolist())

        duration = time.time() - start
        log_pipeline_run(conn, 'inventory', trigger_source,
                         len(df), 0, 'success', duration)
        print(f"Inventory loaded: {len(df)} records in {duration:.2f}s")

    except Exception as e:
        duration = time.time() - start
        log_pipeline_run(conn, 'inventory', trigger_source,
                         0, 0, 'error', duration, str(e))
        print(f"Inventory load failed: {e}")
        raise

def load_transport(conn, df, trigger_source="manual"):
    start = time.time()
    try:
        conn.execute("DELETE FROM transport")
        conn.executemany("""
            INSERT INTO transport VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, df[['lane_id','zone_id','origin','destination',
                 'carrier','mode','distance_km',
                 'planned_transit_days','actual_transit_days',
                 'on_time','delay_days','cost_per_kg_inr',
                 'damage_rate_pct','performance_score',
                 'last_updated']].values.tolist())

        duration = time.time() - start
        log_pipeline_run(conn, 'transport', trigger_source,
                         len(df), 0, 'success', duration)
        print(f"Transport loaded: {len(df)} records in {duration:.2f}s")

    except Exception as e:
        duration = time.time() - start
        log_pipeline_run(conn, 'transport', trigger_source,
                         0, 0, 'error', duration, str(e))
        print(f"Transport load failed: {e}")
        raise

def load_shipments(conn, df, trigger_source="manual"):
    start = time.time()
    try:
        conn.execute("DELETE FROM shipments")
        conn.executemany("""
            INSERT INTO shipments VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, df[['shipment_id','order_id','zone_id','lane_id',
                 'origin','customer','category','carrier',
                 'status','dispatch_date','planned_delivery',
                 'actual_delivery','delay_days','weight_kg',
                 'value_inr','pod_received',
                 'last_updated']].values.tolist())

        duration = time.time() - start
        log_pipeline_run(conn, 'shipments', trigger_source,
                         len(df), 0, 'success', duration)
        print(f"Shipments loaded: {len(df)} records in {duration:.2f}s")

    except Exception as e:
        duration = time.time() - start
        log_pipeline_run(conn, 'shipments', trigger_source,
                         0, 0, 'error', duration, str(e))
        print(f"Shipments load failed: {e}")
        raise

def load_all(inv, trn, shp, sal, fct, trigger_source="manual"):
    conn = duckdb.connect(DB_PATH)
    print(f"Load starting at {datetime.now().strftime('%H:%M:%S')}")

    load_inventory(conn, inv, trigger_source)
    load_transport(conn, trn, trigger_source)
    load_shipments(conn, shp, trigger_source)

    # Log overall pipeline completion
    log_pipeline_run(conn, 'all_tables', trigger_source,
                     len(inv) + len(trn) + len(shp),
                     0, 'success', 0)

    conn.close()
    print(f"Load complete at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    from extract import extract_all
    from transform import transform_all

    inventory, transport, shipments, sales, forecasts = extract_all()
    inv, trn, shp, sal, fct = transform_all(
        inventory, transport, shipments, sales, forecasts)
    load_all(inv, trn, shp, sal, fct)