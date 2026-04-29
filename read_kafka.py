from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    "supply_chain.public.inventory",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    consumer_timeout_ms=5000,
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

print("Reading inventory change events from Kafka...\n")

for msg in consumer:
    payload = msg.value.get("payload", {})
    op      = payload.get("op")
    before  = payload.get("before")
    after   = payload.get("after")

    op_label = {
        "r": "READ (snapshot)",
        "c": "INSERT",
        "u": "UPDATE",
        "d": "DELETE"
    }.get(op, op)

    print(f"Operation: {op_label}")
    if before:
        print(f"  Before: stock={before.get('current_stock')} status={before.get('status')}")
    if after:
        print(f"  After:  stock={after.get('current_stock')} status={after.get('status')} sku={after.get('sku_id')} zone={after.get('zone_id')}")
    print()