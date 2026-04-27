import pandas as pd
from datetime import date

def transform_inventory(inventory_df):
    df = inventory_df.copy()

    # Recalculate days of stock using Python - never trust LLM for math
    df['days_of_stock'] = (df['current_stock'] / 
                           df['avg_daily_demand']).round(1)

    # Reorder quantity needed to get back to safe level
    df['reorder_qty'] = ((df['reorder_point'] * 1.5) - 
                          df['current_stock']).clip(lower=0).astype(int)

    # Days overdue for reorder
    df['days_overdue'] = (df['lead_time_days'] - 
                           df['days_of_stock']).round(1)

    # Stock value at risk
    df['stock_value'] = (df['current_stock'] * 
                          df['unit_cost_inr']).round(2)

    # Urgency classification
    def classify(row):
        stock = row['current_stock']
        rop   = row['reorder_point']
        if stock < rop * 0.5:
            return 'CRITICAL'
        elif stock < rop:
            return 'WARNING'
        return 'HEALTHY'

    df['status'] = df.apply(classify, axis=1)

    # Action label based on urgency
    def action(row):
        if row['status'] == 'CRITICAL':
            days = max(0, round(row['days_overdue'], 1))
            return f"Order immediately - {days} days overdue"
        elif row['status'] == 'WARNING':
            return "Reorder soon"
        return "Stock level OK"

    df['action_required'] = df.apply(action, axis=1)

    return df

def transform_transport(transport_df):
    df = transport_df.copy()

    # Recalculate performance score in Python
    df['performance_score'] = (
        (df['on_time'].astype(int) * 40) +
        (df['damage_rate_pct'].apply(lambda x: max(0, 30 - x * 6))) +
        (df['delay_days'].apply(lambda x: max(0, 30 - x * 10)))
    ).round(1)

    # Classify carrier performance
    def carrier_status(score):
        if score >= 80:
            return 'Good'
        elif score >= 60:
            return 'Average'
        return 'Poor'

    df['carrier_status'] = df['performance_score'].apply(carrier_status)

    return df

def transform_shipments(shipments_df):
    df = shipments_df.copy()
    today = date(2026, 4, 21)

    # Recalculate delay days in Python
    def calc_delay(row):
        if row['status'] == 'Delivered' and row['actual_delivery']:
            return max(0, (pd.to_datetime(row['actual_delivery']).date() - 
                          pd.to_datetime(row['planned_delivery']).date()).days)
        elif row['status'] in ['Delayed','Held at Hub','Lost in Transit']:
            return max(0, (today - 
                          pd.to_datetime(row['planned_delivery']).date()).days)
        return 0

    df['delay_days'] = df.apply(calc_delay, axis=1)

    # Risk classification
    def risk(row):
        if row['status'] == 'Lost in Transit':
            return 'Critical'
        elif row['status'] == 'Delayed' and row['delay_days'] > 3:
            return 'High'
        elif row['status'] in ['Delayed','Held at Hub']:
            return 'Medium'
        elif row['status'] == 'In Transit':
            return 'Low'
        return 'None'

    df['risk_level'] = df.apply(risk, axis=1)

    return df

def transform_sales(sales_df):
    df = sales_df.copy()

    # Calculate revenue per sale
    df['revenue'] = (df['quantity_sold'] * df['price_inr']).round(2)

    # Flag weekend sales
    df['is_weekend'] = pd.to_datetime(df['sale_date']).dt.weekday >= 5

    return df

def transform_forecasts(forecasts_df):
    df = forecasts_df.copy()

    # Flag SKUs where forecast demand exceeds current stock
    df['stockout_risk'] = df['forecasted_demand'] > (
        df['current_stock'] / df['avg_daily_demand'] * 
        df['forecasted_demand']
    )

    # Days until stockout based on forecast
    df['days_until_stockout'] = (
        df['current_stock'] / df['forecasted_demand']
    ).round(1)

    return df

def transform_all(inventory, transport, shipments, sales, forecasts):
    print("Transform starting...")

    inv  = transform_inventory(inventory)
    print(f"Inventory transformed: {len(inv)} records")

    trn  = transform_transport(transport)
    print(f"Transport transformed: {len(trn)} records")

    shp  = transform_shipments(shipments)
    print(f"Shipments transformed: {len(shp)} records")

    sal  = transform_sales(sales)
    print(f"Sales transformed: {len(sal):,} records")

    fct  = transform_forecasts(forecasts)
    print(f"Forecasts transformed: {len(fct)} records")

    print("Transform complete")
    return inv, trn, shp, sal, fct

if __name__ == "__main__":
    from extract import extract_all
    inventory, transport, shipments, sales, forecasts = extract_all()
    inv, trn, shp, sal, fct = transform_all(
        inventory, transport, shipments, sales, forecasts)
    print("\nSample transformed inventory:")
    print(inv[['sku_id','zone_id','status',
               'days_of_stock','reorder_qty',
               'action_required']].head(3))