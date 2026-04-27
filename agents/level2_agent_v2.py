"""
Level 2 Warehouse Stock Agent v2
Python handles all calculations. Gemma 4 explains only.
Run with: python level2_agent_v2.py
"""

import json, os, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from calculations import load_and_calculate, get_summary_stats, get_display_cols_critical, get_display_cols_warning

# ── CONFIG ───────────────────────────────────────────────────
EXCEL_FILE     = "fmcg_warehouse_inventory.xlsx"
MEMORY_FILE    = "agent_memory.json"
SENDER_EMAIL   = "gargikulkarni1999@gmail.com"
SENDER_PASS    = "ihbq xqcm iqkm jnku"
RECEIVER_EMAIL = "gargikulkarni1999@gmail.com"

# ── Memory ───────────────────────────────────────────────────
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {"critical": [], "warning": [], "last_run": None}

def save_memory(critical, warning):
    with open(MEMORY_FILE, "w") as f:
        json.dump({
            "critical": list(critical["SKU"]),
            "warning":  list(warning["SKU"]),
            "last_run": datetime.now().strftime("%Y-%m-%d %H:%M")
        }, f, indent=2)

def find_new(current_df, previous_skus):
    return current_df[~current_df["SKU"].isin(previous_skus)]

# ── AI summary (explains numbers, doesn't calculate them) ────
def generate_summary(stats, new_critical):
    llm = OllamaLLM(model="gemma4:e2b")
    prompt = PromptTemplate.from_template("""
You are a warehouse analyst. These numbers are Python-calculated and accurate.
Write a 3-sentence professional summary. Do NOT recalculate anything.

FACTS:
- Total SKUs: {total_skus}
- Critical: {critical_count} ({critical_pct}%)
- Warning: {warning_count}
- Most urgent: {most_urgent_sku} — {most_urgent_days} days of stock left
- New critical items this run: {new_count}
- Total reorder units needed: {total_reorder_qty}

Write the summary now:
""")
    return llm.invoke(prompt.format(**stats, new_count=len(new_critical)))

# ── HTML email ───────────────────────────────────────────────
def build_email(critical, warning, healthy, stats, new_critical, ai_summary):
    now = datetime.now().strftime("%d %b %Y, %H:%M")

    def rows(df_section, color):
        out = ""
        for _, r in df_section.iterrows():
            out += f"<tr><td style='padding:8px;border-bottom:1px solid #eee'>{r['SKU']}</td><td style='padding:8px;border-bottom:1px solid #eee'>{r['Product Name']}</td><td style='padding:8px;border-bottom:1px solid #eee'>{r['Category']}</td><td style='padding:8px;border-bottom:1px solid #eee;color:{color};font-weight:600'>{r['Days of Stock Left']} days</td><td style='padding:8px;border-bottom:1px solid #eee'>{r['Reorder Qty Needed']} units</td><td style='padding:8px;border-bottom:1px solid #eee'>{r['Action Required']}</td></tr>"
        return out

    new_section = ""
    if len(new_critical) > 0:
        new_section = f"""
        <div style='padding:20px 24px 0;background:white'>
            <h3 style='color:#c62828;margin:0 0 12px'>🆕 New Critical Items ({len(new_critical)})</h3>
            <table style='width:100%;border-collapse:collapse;font-size:13px'>
                <tr style='background:#fce4ec'>
                    <th style='padding:8px;text-align:left'>SKU</th><th style='padding:8px;text-align:left'>Product</th>
                    <th style='padding:8px;text-align:left'>Category</th><th style='padding:8px;text-align:left'>Days Left</th>
                    <th style='padding:8px;text-align:left'>Order Qty</th><th style='padding:8px;text-align:left'>Action</th>
                </tr>
                {rows(new_critical, "#c62828")}
            </table>
        </div>"""

    return f"""
    <html><body style='font-family:Arial,sans-serif;max-width:700px;margin:auto;color:#333'>
    <div style='background:#1F4E79;padding:20px 24px;border-radius:8px 8px 0 0'>
        <h2 style='color:white;margin:0'>📦 Warehouse Stock Report</h2>
        <p style='color:#b3d1f0;margin:4px 0 0'>{now}</p>
    </div>
    <div style='background:#f8f9fa;padding:16px 24px;border-left:4px solid #1F4E79'>
        <p style='margin:0;font-size:14px;line-height:1.6'>{ai_summary}</p>
    </div>
    <div style='display:flex;gap:12px;padding:20px 24px 0;background:white'>
        <div style='flex:1;background:#fce4ec;border-radius:8px;padding:14px;text-align:center'>
            <div style='font-size:28px;font-weight:700;color:#c62828'>{stats["critical_count"]}</div>
            <div style='font-size:12px;color:#c62828'>Critical</div></div>
        <div style='flex:1;background:#fff9c4;border-radius:8px;padding:14px;text-align:center'>
            <div style='font-size:28px;font-weight:700;color:#f9a825'>{stats["warning_count"]}</div>
            <div style='font-size:12px;color:#f9a825'>Warning</div></div>
        <div style='flex:1;background:#e8f5e9;border-radius:8px;padding:14px;text-align:center'>
            <div style='font-size:28px;font-weight:700;color:#2e7d32'>{stats["healthy_count"]}</div>
            <div style='font-size:12px;color:#2e7d32'>Healthy</div></div>
        <div style='flex:1;background:#e3f2fd;border-radius:8px;padding:14px;text-align:center'>
            <div style='font-size:28px;font-weight:700;color:#1565c0'>{stats["total_reorder_qty"]:,}</div>
            <div style='font-size:12px;color:#1565c0'>Units to Reorder</div></div>
    </div>
    {new_section}
    <div style='padding:20px 24px 0;background:white'>
        <h3 style='color:#c62828;margin:0 0 12px'>🔴 All Critical SKUs</h3>
        <table style='width:100%;border-collapse:collapse;font-size:13px'>
            <tr style='background:#fce4ec'>
                <th style='padding:8px;text-align:left'>SKU</th><th style='padding:8px;text-align:left'>Product</th>
                <th style='padding:8px;text-align:left'>Category</th><th style='padding:8px;text-align:left'>Days Left</th>
                <th style='padding:8px;text-align:left'>Order Qty</th><th style='padding:8px;text-align:left'>Action</th>
            </tr>
            {rows(critical, "#c62828")}
        </table>
    </div>
    <div style='padding:20px 24px;background:white'>
        <h3 style='color:#f9a825;margin:0 0 12px'>🟡 Warning SKUs</h3>
        <table style='width:100%;border-collapse:collapse;font-size:13px'>
            <tr style='background:#fff9c4'>
                <th style='padding:8px;text-align:left'>SKU</th><th style='padding:8px;text-align:left'>Product</th>
                <th style='padding:8px;text-align:left'>Category</th><th style='padding:8px;text-align:left'>Days Left</th>
                <th style='padding:8px;text-align:left'>Order Qty</th><th style='padding:8px;text-align:left'>Action</th>
            </tr>
            {rows(warning, "#f9a825")}
        </table>
    </div>
    <div style='background:#f8f9fa;padding:14px 24px;border-radius:0 0 8px 8px;font-size:12px;color:#888'>
        All calculations by Python · Narrative by Gemma 4 (local) · {now}
    </div>
    </body></html>"""

# ── Send Gmail ───────────────────────────────────────────────
def send_email(html, stats, new_count):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📦 Warehouse Alert — {stats['critical_count']} Critical SKUs ({new_count} new) · {datetime.now().strftime('%d %b %Y')}"
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECEIVER_EMAIL
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(SENDER_EMAIL, SENDER_PASS)
        s.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

# ── Main ─────────────────────────────────────────────────────
def run():
    print(f"\n{'='*50}")
    print(f"  Warehouse Agent v2 — {datetime.now().strftime('%d %b %Y, %H:%M')}")
    print(f"{'='*50}\n")

    print("  Loading & calculating inventory data...")
    df, critical, warning, healthy = load_and_calculate(EXCEL_FILE)
    stats = get_summary_stats(df, critical, warning, healthy)
    print(f"  Critical: {stats['critical_count']}  Warning: {stats['warning_count']}  Healthy: {stats['healthy_count']}")
    print(f"  Most urgent: {stats['most_urgent_sku']} — {stats['most_urgent_days']} days left")
    print(f"  Total reorder qty needed: {stats['total_reorder_qty']:,} units\n")

    print("  Checking memory from last run...")
    memory = load_memory()
    new_critical = find_new(critical, memory["critical"])
    new_warning  = find_new(warning,  memory["warning"])
    print(f"  New critical items: {len(new_critical)}")

    if len(critical) == 0:
        print("  No critical items. No email sent.")
        save_memory(critical, warning)
        return

    print("\n  Generating AI narrative (Gemma 4)...")
    summary = generate_summary(stats, new_critical)
    print(f"  Summary: {summary[:80]}...\n")

    print("  Building & sending email...")
    html = build_email(critical, warning, healthy, stats, new_critical, summary)
    try:
        send_email(html, stats, len(new_critical))
        print("  Email sent successfully. Check your inbox!")
    except Exception as e:
        print(f"  Email failed: {e}")
        print("  Check your App Password at myaccount.google.com/apppasswords")

    save_memory(critical, warning)
    print(f"\n{'='*50}\n")

if __name__ == "__main__":
    run()
