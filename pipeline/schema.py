import psycopg2
import os
from dotenv import load_dotenv

# PostgreSQL connection settings
load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def create_schema():
    conn = get_connection()
    cur  = conn.cursor()
    print("Connected to PostgreSQL...")

    # Zones master table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS zones (
            zone_id           VARCHAR(2) PRIMARY KEY,
            zone_name         VARCHAR(100),
            city              VARCHAR(100),
            region            VARCHAR(100),
            warehouse_address VARCHAR(200),
            latitude          FLOAT,
            longitude         FLOAT,
            capacity_sqft     INTEGER,
            manager_name      VARCHAR(100)
        )
    """)
    print("zones table created")

    # Inventory table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            sku_id            VARCHAR(20),
            zone_id           VARCHAR(2) REFERENCES zones(zone_id),
            product_name      VARCHAR(200),
            category          VARCHAR(100),
            current_stock     INTEGER,
            reorder_point     INTEGER,
            avg_daily_demand  INTEGER,
            lead_time_days    INTEGER,
            supplier          VARCHAR(200),
            unit_cost_inr     FLOAT,
            days_of_stock     FLOAT,
            reorder_qty       INTEGER,
            status            VARCHAR(20),
            action_required   VARCHAR(200),
            last_updated      TIMESTAMP,
            PRIMARY KEY (sku_id, zone_id)
        )
    """)
    print("inventory table created")

    # Transport table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transport (
            lane_id              VARCHAR(20) PRIMARY KEY,
            zone_id              VARCHAR(2) REFERENCES zones(zone_id),
            origin               VARCHAR(100),
            destination          VARCHAR(100),
            carrier              VARCHAR(100),
            mode                 VARCHAR(50),
            distance_km          INTEGER,
            planned_transit_days INTEGER,
            actual_transit_days  INTEGER,
            on_time              BOOLEAN,
            delay_days           INTEGER,
            cost_per_kg_inr      FLOAT,
            damage_rate_pct      FLOAT,
            performance_score    FLOAT,
            last_updated         TIMESTAMP
        )
    """)
    print("transport table created")

    # Shipments table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id       VARCHAR(20) PRIMARY KEY,
            order_id          VARCHAR(20),
            zone_id           VARCHAR(2) REFERENCES zones(zone_id),
            lane_id           VARCHAR(20) REFERENCES transport(lane_id),
            origin            VARCHAR(100),
            customer          VARCHAR(200),
            category          VARCHAR(100),
            carrier           VARCHAR(100),
            status            VARCHAR(50),
            dispatch_date     DATE,
            planned_delivery  DATE,
            actual_delivery   DATE,
            delay_days        INTEGER,
            weight_kg         FLOAT,
            value_inr         FLOAT,
            pod_received      BOOLEAN,
            last_updated      TIMESTAMP
        )
    """)
    print("shipments table created")

    # Sales table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id        VARCHAR(20) PRIMARY KEY,
            zone_id        VARCHAR(2) REFERENCES zones(zone_id),
            sku_id         VARCHAR(20),
            product_name   VARCHAR(200),
            category       VARCHAR(100),
            quantity_sold  INTEGER,
            sale_date      DATE,
            customer       VARCHAR(200),
            channel        VARCHAR(50),
            price_inr      FLOAT,
            promotion_flag BOOLEAN,
            last_updated   TIMESTAMP
        )
    """)
    print("sales table created")

    # Forecasts table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            forecast_id       VARCHAR(20) PRIMARY KEY,
            zone_id           VARCHAR(2) REFERENCES zones(zone_id),
            sku_id            VARCHAR(20),
            forecast_date     DATE,
            forecasted_demand FLOAT,
            rolling_avg_30d   FLOAT,
            upper_bound       FLOAT,
            lower_bound       FLOAT,
            generated_at      TIMESTAMP
        )
    """)
    print("forecasts table created")

    # Pipeline log table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_log (
            log_id          VARCHAR(50) PRIMARY KEY,
            run_timestamp   TIMESTAMP,
            table_affected  VARCHAR(50),
            trigger_source  VARCHAR(50),
            rows_inserted   INTEGER,
            rows_updated    INTEGER,
            status          VARCHAR(20),
            duration_seconds FLOAT,
            error_message   TEXT
        )
    """)
    print("pipeline_log table created")

    conn.commit()
    cur.close()
    conn.close()
    print("All 7 tables created in PostgreSQL")

if __name__ == "__main__":
    create_schema()