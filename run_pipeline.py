import sys
import os

# Add pipeline folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'pipeline'))

from extract import extract_all
from transform import transform_all
from load import load_all

def run(trigger_source="manual"):
    print("Pipeline starting...")
    inventory, transport, shipments, sales, forecasts = extract_all()
    inv, trn, shp, sal, fct = transform_all(
        inventory, transport, shipments, sales, forecasts)
    load_all(inv, trn, shp, sal, fct, trigger_source)
    print("Pipeline complete")

if __name__ == "__main__":
    run()