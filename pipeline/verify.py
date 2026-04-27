import duckdb
import os


DB_PATH = os.path.join(os.path.dirname(__file__), "../database/supply_chain.duckdb")

conn = duckdb.connect(DB_PATH)

# Show all tables
print("Tables in database:")
print(conn.execute("SHOW TABLES").fetchdf())

# Show inventory schema
print("\nInventory table columns:")
print(conn.execute("Select * from zones").fetchdf())

print("\nInventory summary:")
print(conn.execute("""
    SELECT 
        zone_id,
        COUNT(*) as total_skus,
        SUM(CASE WHEN status='CRITICAL' THEN 1 ELSE 0 END) as critical,
        SUM(CASE WHEN status='WARNING'  THEN 1 ELSE 0 END) as warning,
        SUM(CASE WHEN status='HEALTHY'  THEN 1 ELSE 0 END) as healthy
    FROM inventory
    GROUP BY zone_id
    ORDER BY zone_id
""").fetchdf())


print("\nTransport summary:")
print(conn.execute("""
    SELECT 
        zone_id,
        COUNT(*) as total_lanes,
        SUM(CASE WHEN on_time=true THEN 1 ELSE 0 END) as on_time_lanes,
        ROUND(AVG(performance_score),1) as avg_perf_score,
        ROUND(AVG(cost_per_kg_inr),2) as avg_cost_per_kg,
        SUM(CASE WHEN delay_days > 0 THEN 1 ELSE 0 END) as delayed_lanes
    FROM transport
    GROUP BY zone_id
    ORDER BY zone_id
""").fetchdf())

print("\nFull database summary:")
print(conn.execute("""
    SELECT 'zones'     as table_name, COUNT(*) as records FROM zones
    UNION ALL
    SELECT 'inventory',               COUNT(*) FROM inventory
    UNION ALL
    SELECT 'transport',               COUNT(*) FROM transport
    UNION ALL
    SELECT 'shipments',               COUNT(*) FROM shipments
    UNION ALL
    SELECT 'sales',                   COUNT(*) FROM sales
    UNION ALL
    SELECT 'forecasts',               COUNT(*) FROM forecasts
""").fetchdf())

print("\nSample forecast — Zone A, first 3 SKUs:")
print(conn.execute("""
    SELECT f.zone_id, f.sku_id, i.product_name,
           f.rolling_avg_30d, f.upper_bound, f.lower_bound
    FROM forecasts f
    JOIN inventory i ON f.sku_id = i.sku_id 
                     AND f.zone_id = i.zone_id
    WHERE f.zone_id = 'A'
    LIMIT 3
""").fetchdf())

conn.close()

