"""
calculations.py
Central Python calculations module — imported by both stock_agent.py and level2_agent.py
All numbers are computed here in Python. LLM never does math.
"""

import pandas as pd

def load_and_calculate(filepath):
    """Load Excel and compute all derived columns in Python."""
    df = pd.read_excel(filepath, sheet_name="Inventory Data")

    # Core calculations — Python does all the math
    df["Days of Stock Left"]     = (df["Current Stock (Units)"] / df["Avg Daily Demand"]).round(1)
    df["Reorder Qty Needed"]     = ((df["Reorder Point (Units)"] * 1.5) - df["Current Stock (Units)"]).clip(lower=0).round(0).astype(int)
    df["Days Overdue for Reorder"] = (df["Lead Time (Days)"] - df["Days of Stock Left"]).round(1)
    df["Stock Value at Risk (INR)"] = (df["Current Stock (Units)"] * df["Unit Cost (INR)"]).round(2)

    # Urgency classification — Python decides, not LLM
    def classify(row):
        stock = row["Current Stock (Units)"]
        rop   = row["Reorder Point (Units)"]
        if stock < rop * 0.5:  return "CRITICAL"
        elif stock < rop:      return "WARNING"
        else:                  return "HEALTHY"

    df["Status"] = df.apply(classify, axis=1)

    # Reorder urgency label
    def urgency(row):
        if row["Status"] == "CRITICAL" and row["Days Overdue for Reorder"] > 0:
            return f"ORDER NOW — {row['Days Overdue for Reorder']} days overdue"
        elif row["Status"] == "CRITICAL":
            return f"Order within {abs(row['Days Overdue for Reorder']):.0f} days"
        elif row["Status"] == "WARNING":
            return "Monitor closely"
        else:
            return "OK"

    df["Action Required"] = df.apply(urgency, axis=1)

    # Split into status groups
    critical = df[df["Status"] == "CRITICAL"].sort_values("Days of Stock Left")
    warning  = df[df["Status"] == "WARNING"].sort_values("Days of Stock Left")
    healthy  = df[df["Status"] == "HEALTHY"]

    return df, critical, warning, healthy

def get_summary_stats(df, critical, warning, healthy):
    """Pre-compute all summary numbers Python-side."""
    return {
        "total_skus":          len(df),
        "critical_count":      len(critical),
        "warning_count":       len(warning),
        "healthy_count":       len(healthy),
        "critical_pct":        round(len(critical) / len(df) * 100, 1),
        "total_stock_value":   round(df["Stock Value at Risk (INR)"].sum(), 2),
        "critical_value":      round(critical["Stock Value at Risk (INR)"].sum(), 2),
        "avg_days_critical":   round(critical["Days of Stock Left"].mean(), 1) if len(critical) > 0 else 0,
        "most_urgent_sku":     critical.iloc[0]["Product Name"] if len(critical) > 0 else "None",
        "most_urgent_days":    critical.iloc[0]["Days of Stock Left"] if len(critical) > 0 else 0,
        "categories_at_risk":  critical["Category"].nunique(),
        "total_reorder_qty":   int(critical["Reorder Qty Needed"].sum()),
    }

def get_display_cols_critical():
    return ["SKU","Product Name","Category","Current Stock (Units)",
            "Reorder Point (Units)","Days of Stock Left",
            "Reorder Qty Needed","Action Required","Supplier"]

def get_display_cols_warning():
    return ["SKU","Product Name","Category","Current Stock (Units)",
            "Reorder Point (Units)","Days of Stock Left","Supplier"]
