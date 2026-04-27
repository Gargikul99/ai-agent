"""shipment_agent.py — analyses active shipments, delays, ETAs"""
import pandas as pd

def load_shipments(filepath="shipment_data.xlsx"):
    df   = pd.read_excel(filepath, sheet_name="Active Shipments")
    summ = pd.read_excel(filepath, sheet_name="Shipment Summary")

    delayed   = df[df["Status"]=="Delayed"].sort_values("Delay (Days)", ascending=False)
    held      = df[df["Status"]=="Held at Hub"]
    lost      = df[df["Status"]=="Lost in Transit"]
    in_transit= df[df["Status"]=="In Transit"]
    pod_pending=df[(df["Status"]=="Delivered")&(df["POD Received"]=="No")]

    stats = {
        "total_shipments":    len(df),
        "delivered":          len(df[df["Status"]=="Delivered"]),
        "in_transit":         len(in_transit),
        "delayed":            len(delayed),
        "held_at_hub":        len(held),
        "lost_in_transit":    len(lost),
        "out_for_delivery":   len(df[df["Status"]=="Out for Delivery"]),
        "avg_delay_days":     round(delayed["Delay (Days)"].mean(),1) if len(delayed)>0 else 0,
        "max_delay_days":     int(delayed["Delay (Days)"].max()) if len(delayed)>0 else 0,
        "pod_pending":        len(pod_pending),
        "total_value_at_risk":round((delayed["Shipment Value (INR)"].sum()+
                                     held["Shipment Value (INR)"].sum()+
                                     lost["Shipment Value (INR)"].sum()),2),
        "most_delayed_carrier": delayed["Carrier"].value_counts().idxmax() if len(delayed)>0 else "N/A",
        "most_affected_customer": delayed["Customer/Destination"].value_counts().idxmax() if len(delayed)>0 else "N/A",
    }
    return df, delayed, held, lost, pod_pending, stats

def get_shipment_context(filepath="shipment_data.xlsx"):
    df, delayed, held, lost, pod_pending, stats = load_shipments(filepath)
    return stats, delayed.head(8), held.head(5), lost.head(5)
