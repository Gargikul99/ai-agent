from kafka import KafkaConsumer
import psycopg2
import json
import logging
from dotenv import load_dotenv
import os


load_dotenv()

# Remove the old basicConfig and replace with this
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s — %(levelname)s — %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST")
)
conn.autocommit = True

def refresh_views():
    with conn.cursor() as cur:
        cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY inventory_summary;")
        cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY zone_summary;")
    logger.info("Both materialized views refreshed successfully.")

# Listen to all relevant Kafka topics
consumer = KafkaConsumer(
    'supply_chain.public.inventory',
    'supply_chain.public.forecasts',
    'supply_chain.public.shipments',
    'supply_chain.public.transport',
    bootstrap_servers='localhost:9092',
    group_id='dashboard-consumer-group',
    auto_offset_reset='latest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

logger.info("Kafka consumer started — listening for changes...")

for msg in consumer:
    payload = msg.value.get('payload', {})
    op = payload.get('op')

    # Only react to actual changes — not snapshot reads
    if op in ['c', 'u', 'd']:
        topic = msg.topic
        logger.info(f"Change detected on {msg.topic} — op: {op} — sku: {payload.get('after', {}).get('sku_id')} — refreshing views...")
        refresh_views()