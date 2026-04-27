"""transport_agent.py — analyses transport lanes and carrier performance"""
import pandas as pd

def load_transport(filepath="transport_data.xlsx"):
    df   = pd.read_excel(filepath, sheet_name="Transport Lanes")
    summ = pd.read_excel(filepath, sheet_name="Carrier Summary")

    delayed     = df[df["On Time"]=="No"].sort_values("Delay (Days)", ascending=False)
    on_time     = df[df["On Time"]=="Yes"]
    poor        = df[df["Performance Score"] < 65].sort_values("Performance Score")
    expensive   = df.nlargest(5, "Cost per KG (INR)")

    stats = {
        "total_lanes":       len(df),
        "delayed_lanes":     len(delayed),
        "on_time_lanes":     len(on_time),
        "on_time_pct":       round(len(on_time)/len(df)*100,1),
        "avg_delay_days":    round(delayed["Delay (Days)"].mean(),1) if len(delayed)>0 else 0,
        "poor_performers":   len(poor),
        "total_carriers":    df["Carrier"].nunique(),
        "worst_carrier":     summ.nsmallest(1,"Avg_Perf_Score")["Carrier"].iloc[0] if len(summ)>0 else "N/A",
        "best_carrier":      summ.nlargest(1,"Avg_Perf_Score")["Carrier"].iloc[0]  if len(summ)>0 else "N/A",
        "avg_cost_per_kg":   round(df["Cost per KG (INR)"].mean(),2),
        "highest_damage_carrier": df.groupby("Carrier")["Damage Rate (%)"].mean().idxmax(),
    }
    return df, delayed, poor, summ, stats

def get_transport_context(filepath="transport_data.xlsx"):
    df, delayed, poor, summ, stats = load_transport(filepath)
    return stats, delayed.head(8), poor.head(5), summ
