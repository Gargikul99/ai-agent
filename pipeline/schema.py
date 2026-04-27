import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(__file__),"../database/supply_chain.duckdb")

def create_schema():
    conn = duckdb.connect(DB_PATH)
    # ── Table 0: Zones (master reference table) ──────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS zones (
            zone_id             VARCHAR PRIMARY KEY,
            zone_name           VARCHAR,
            city                VARCHAR,
            region              VARCHAR,
            warehouse_address   VARCHAR,
            latitude            FLOAT,
            longitude           FLOAT,
            capacity_sqft       INTEGER,
            manager_name        VARCHAR
        )
    """)
    print("✅ zones table created")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            sku_id              VARCHAR,
            zone_id             VARCHAR,
            product_name        VARCHAR,
            category            VARCHAR,
            current_stock       INTEGER,
            reorder_point       INTEGER,
            avg_daily_demand    INTEGER,
            lead_time_days      INTEGER,
            supplier            VARCHAR,
            unit_cost_inr       FLOAT,
            days_of_stock       FLOAT,
            reorder_qty         INTEGER,
            status              VARCHAR,
            action_required     VARCHAR,
            last_updated        TIMESTAMP,
            PRIMARY KEY (sku_id, zone_id)
        )
    """)
    print("✅ inventory table created")

    # ── Table 2: Transport ───────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transport (
            lane_id             VARCHAR PRIMARY KEY,
            zone_id             VARCHAR,
            origin              VARCHAR,
            destination         VARCHAR,
            carrier             VARCHAR,
            mode                VARCHAR,
            distance_km         INTEGER,
            planned_transit_days INTEGER,
            actual_transit_days  INTEGER,
            on_time             BOOLEAN,
            delay_days          INTEGER,
            cost_per_kg_inr     FLOAT,
            damage_rate_pct     FLOAT,
            performance_score   FLOAT,
            last_updated        TIMESTAMP
        )
    """)
    print("✅ transport table created")

    # ── Table 3: Shipments ───────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id         VARCHAR PRIMARY KEY,
            order_id            VARCHAR,
            zone_id             VARCHAR,
            lane_id             VARCHAR,
            origin              VARCHAR,
            customer            VARCHAR,
            category            VARCHAR,
            carrier             VARCHAR,
            status              VARCHAR,
            dispatch_date       DATE,
            planned_delivery    DATE,
            actual_delivery     DATE,
            delay_days          INTEGER,
            weight_kg           FLOAT,
            value_inr           FLOAT,
            pod_received        BOOLEAN,
            last_updated        TIMESTAMP
        )
    """)
    print("✅ shipments table created")

    # ── Table 4: Sales ───────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id             VARCHAR PRIMARY KEY,
            zone_id             VARCHAR,
            sku_id              VARCHAR,
            product_name        VARCHAR,
            category            VARCHAR,
            quantity_sold       INTEGER,
            sale_date           DATE,
            customer            VARCHAR,
            channel             VARCHAR,
            price_inr           FLOAT,
            promotion_flag      BOOLEAN,
            last_updated        TIMESTAMP
        )
    """)
    print("✅ sales table created")

    # ── Table 5: Forecasts ───────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            forecast_id         VARCHAR PRIMARY KEY,
            zone_id             VARCHAR,
            sku_id              VARCHAR,
            forecast_date       DATE,
            forecasted_demand   FLOAT,
            rolling_avg_30d     FLOAT,
            upper_bound         FLOAT,
            lower_bound         FLOAT,
            generated_at        TIMESTAMP
        )
    """)
    print("✅ forecasts table created")

    # ── Table 6: Pipeline Log ────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_log (
            log_id              VARCHAR PRIMARY KEY,
            run_timestamp       TIMESTAMP,
            table_affected      VARCHAR,
            trigger_source      VARCHAR,
            rows_inserted       INTEGER,
            rows_updated        INTEGER,
            status              VARCHAR,
            duration_seconds    FLOAT,
            error_message       VARCHAR
        )
    """)
    print("✅ pipeline_log table created")

    conn.close()
    print("\n✅ All 6 tables created successfully in DuckDB")

if __name__ == "__main__":
    create_schema()