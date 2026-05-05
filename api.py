from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import pandas as pd
import os
import json
from typing import List
from dotenv import load_dotenv
from datetime import datetime

import hashlib

def route_offset(shipment_id, index):
    # Deterministic small offset based on shipment ID
    hash_val = int(hashlib.md5(shipment_id.encode()).hexdigest(), 16)
    offset_lat = ((hash_val % 20) - 10) * 0.05
    offset_lng = (((hash_val >> 8) % 20) - 10) * 0.05
    return offset_lat, offset_lng

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_clients: List[WebSocket] = []

from sqlalchemy import create_engine

def get_engine():
    return create_engine(
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )

def health_status(status: str) -> str:
    if status == "CRITICAL": return "critical"
    if status == "WARNING":  return "warning"
    return "healthy"

def carrier_status(score: float) -> str:
    if score < 50: return "critical"
    if score < 70: return "warning"
    return "healthy"

# ── GET /inventory ─────────────────────────────────────────────────
@app.get("/api/inventory")
def inventory():
   

    # KPIs from zone_summary
    zs = pd.read_sql("SELECT * FROM zone_summary", get_engine())
    total_skus    = int(zs["total_skus"].sum())
    total_stock   = int(zs["total_stock"].sum())
    critical_skus = int(zs["critical_skus"].sum())
    warning_skus  = int(zs["warning_skus"].sum())
    total_value   = round(float(zs["total_inventory_value_usd"].sum()), 2)

    kpis = [
        {
            "label": "Total SKUs",
            "value": total_skus,
            "status": "healthy"
        },
        {
            "label": "Low Stock",
            "value": warning_skus,
            "delta": f"+{warning_skus}",
            "status": "warning" if warning_skus > 0 else "healthy"
        },
        {
            "label": "Out of Stock",
            "value": critical_skus,
            "delta": f"+{critical_skus}",
            "status": "critical" if critical_skus > 0 else "healthy"
        },
        {
            "label": "Stock Value",
            "value": f"${total_value:,.0f}",
            "status": "healthy"
        }
    ]

    # Low stock items from inventory_summary
    inv = pd.read_sql("""
        SELECT sku_id, product_name, city, current_stock,
               reorder_point, zone_id, status
        FROM inventory_summary
        WHERE status IN ('CRITICAL','WARNING')
        ORDER BY days_of_stock ASC
        LIMIT 20
    """, get_engine())

    low_stock = [
    {
        "sku": f"{row['sku_id']}-{row['zone_id']}",  # ← make unique
        "name": row["product_name"],
        "warehouse": row["city"],
        "onHand": int(row["current_stock"]),
        "reorderPoint": int(row["reorder_point"]),
        "status": health_status(row["status"])
    }
    for _, row in inv.iterrows()
]

    # By warehouse from zone_summary
    by_warehouse = [
        {
            "warehouse": row["city"],
            "units": int(row["total_stock"])
        }
        for _, row in zs.iterrows()
    ]

    
    return {
        "kpis": kpis,
        "lowStock": low_stock,
        "byWarehouse": by_warehouse,
        "updatedAt": datetime.now().isoformat()
    }

# ── GET /shipments ─────────────────────────────────────────────────
@app.get("/api/shipments")
def shipments():
    

    sh = pd.read_sql("""
    SELECT s.shipment_id, s.origin, s.customer,
           s.carrier, s.status, s.delay_days,
           s.planned_delivery, s.value_usd,
           s.destination_city,
           s.dest_latitude, s.dest_longitude,
           z.city, z.latitude AS origin_lat, 
           z.longitude AS origin_lng
    FROM shipments s
    JOIN zones z ON s.zone_id = z.zone_id
    ORDER BY s.delay_days DESC
""", get_engine())

    zs = pd.read_sql("""
        SELECT SUM(total_shipments)    AS total,
               SUM(delayed_shipments)  AS delayed,
               SUM(pod_pending)        AS pod_pending,
               ROUND(AVG(avg_carrier_performance)::numeric, 1) AS avg_perf
        FROM zone_summary
    """, get_engine())

    total      = int(zs.iloc[0]["total"])
    delayed    = int(zs.iloc[0]["delayed"])
    pod        = int(zs.iloc[0]["pod_pending"])
    on_time    = total - delayed
    on_time_pct = round(on_time / max(total, 1) * 100, 1)

    kpis = [
        {
            "label": "In Transit",
            "value": int(sh[sh["status"] == "In Transit"].shape[0]),
            "status": "healthy"
        },
        {
            "label": "On Time",
            "value": f"{on_time_pct}%",
            "status": "healthy" if on_time_pct >= 75 else "warning"
        },
        {
            "label": "Delayed",
            "value": delayed,
            "delta": f"+{delayed}",
            "status": "critical" if delayed > 5 else "warning"
        },
        {
            "label": "POD Pending",
            "value": pod,
            "status": "warning" if pod > 0 else "healthy"
        }
    ]

    def shipment_status(row):
        if row["status"] == "Delayed": return "critical"
        if row["delay_days"] > 0:      return "warning"
        return "healthy"

    in_transit = [
    {
        "id": row["shipment_id"],
        "origin": row["origin"],
        "destination": row["destination_city"] or row["city"],
        "carrier": row["carrier"],
        "eta": str(row["planned_delivery"]),
        "status": shipment_status(row),
        "delayHours": int(row["delay_days"]) * 24,
        "lat": float(row["origin_lat"]) if row["origin_lat"] else None,
        "lng": float(row["origin_lng"]) if row["origin_lng"] else None,
        "originCoords": [
            float(row["origin_lat"]) + route_offset(row["shipment_id"], i)[0],
            float(row["origin_lng"]) + route_offset(row["shipment_id"], i)[1]
        ],
        "destinationCoords": [
            float(row["dest_latitude"]) if row["dest_latitude"] else 0,
            float(row["dest_longitude"]) if row["dest_longitude"] else 0
        ],
        "progress": 0.5
    }
    for i, (_, row) in enumerate(sh.iterrows())
]

    by_status = sh.groupby("status").size().reset_index(name="count")
    by_status_list = [
        {"status": row["status"], "count": int(row["count"])}
        for _, row in by_status.iterrows()
    ]

   
    return {
        "kpis": kpis,
        "inTransit": in_transit,
        "byStatus": by_status_list,
        "updatedAt": datetime.now().isoformat()
    }

# ── GET /orders ────────────────────────────────────────────────────
@app.get("/api/orders")
def orders():
    # Orders table not built yet — returns structured mock
    # Will use real data in v1.4
    now = datetime.now().isoformat()
    return {
        "kpis": [
            {"label": "Orders Today",     "value": 0,    "status": "healthy"},
            {"label": "Fulfillment Rate", "value": "0%", "status": "healthy"},
            {"label": "Backorders",       "value": 0,    "status": "healthy"},
            {"label": "Cancelled",        "value": 0,    "status": "healthy"},
        ],
        "recent": [],
        "fulfillmentTrend": [],
        "updatedAt": now
    }

# ── GET /suppliers ─────────────────────────────────────────────────
@app.get("/api/suppliers")
def suppliers():
  

    sup = pd.read_sql("""
        SELECT
            i.supplier,
            ROUND(AVG(i.lead_time_days)::numeric, 0)    AS avg_lead_days,
            COUNT(DISTINCT i.sku_id)                     AS total_skus,
            COUNT(DISTINCT CASE WHEN i.status = 'CRITICAL'
                  THEN i.sku_id END)                     AS critical_skus,
            ROUND(AVG(t.performance_score)::numeric, 1)  AS avg_performance
        FROM inventory_summary i
        LEFT JOIN transport t ON i.zone_id = t.zone_id
        GROUP BY i.supplier
        ORDER BY critical_skus DESC
    """, get_engine())

    total_suppliers = len(sup)
    at_risk = int(sup[sup["critical_skus"] > 0].shape[0])
    avg_lead = round(float(sup["avg_lead_days"].mean()), 1)

    kpis = [
        {
            "label": "Active Suppliers",
            "value": total_suppliers,
            "status": "healthy"
        },
        {
            "label": "Avg Lead Time",
            "value": f"{avg_lead}d",
            "status": "warning" if avg_lead > 10 else "healthy"
        },
        {
            "label": "Open POs",
            "value": 0,
            "status": "healthy"
        },
        {
            "label": "At Risk",
            "value": at_risk,
            "status": "critical" if at_risk > 0 else "healthy"
        }
    ]

    def sup_status(row):
        perf = float(row["avg_performance"]) if row["avg_performance"] else 70
        if perf < 40:   return "critical"
        if perf < 60:   return "warning"
        return "healthy"

    supplier_list = [
        {
            "id": f"SUP-{i+1:03d}",
            "name": row["supplier"],
            "region": "AMER",
            "onTimeRate": round(float(row["avg_performance"]) / 100, 2)
                          if row["avg_performance"] else 0.8,
            "leadTimeDays": int(row["avg_lead_days"]),
            "status": sup_status(row)
        }
        for i, (_, row) in enumerate(sup.iterrows())
    ]


    return {
        "kpis": kpis,
        "suppliers": supplier_list,
        "updatedAt": datetime.now().isoformat()
    }

# ── GET /po/drafts ─────────────────────────────────────────────────
@app.get("/api/po/drafts")
def po_drafts():


    # Get critical SKUs to generate draft POs
    critical = pd.read_sql("""
        SELECT sku_id, zone_id, product_name, city,
               current_stock, reorder_point, avg_daily_demand,
               reorder_qty, supplier, unit_cost_usd,
               days_of_stock, status
        FROM inventory_summary
        WHERE status = 'CRITICAL'
        ORDER BY days_of_stock ASC
        LIMIT 10
    """, get_engine())
    

    now = datetime.now().isoformat()

    drafts = [
        {
            "id": f"PO-DRAFT-{i+1:04d}",
            "sku": row["sku_id"],
            "productName": row["product_name"],
            "warehouse": row["city"],
            "onHand": int(row["current_stock"]),
            "reorderPoint": int(row["reorder_point"]),
            "avgDailyDemand": int(row["avg_daily_demand"]),
            "suggestedQty": int(row["reorder_qty"]),
            "suggestedSupplier": {
                "supplierId": f"SUP-{i+1:03d}",
                "supplierName": row["supplier"],
                "unitPrice": float(row["unit_cost_usd"]),
                "leadTimeDays": 5,
                "onTimeRate": 0.92,
                "score": 0.85
            },
            "alternativeSuppliers": [],
            "unitPrice": float(row["unit_cost_usd"]),
            "totalCost": round(float(row["unit_cost_usd"]) *
                               float(row["reorder_qty"]), 2),
            "estimatedEta": "2026-05-10",
            "rationale": f"Stock at {row['days_of_stock']} days — "
                         f"reorder point of {row['reorder_point']} units breached",
            "urgency": "critical",
            "createdAt": now,
            "status": "pending_approval"
        }
        for i, (_, row) in enumerate(critical.iterrows())
    ]

    total_spend = sum(d["totalCost"] for d in drafts)

    return {
        "drafts": drafts,
        "placed": [],
        "kpis": [
            {
                "label": "Awaiting Approval",
                "value": len(drafts),
                "status": "warning"
            },
            {
                "label": "Critical Drafts",
                "value": len(drafts),
                "status": "critical"
            },
            {
                "label": "Pending Spend",
                "value": f"${total_spend:,.0f}",
                "status": "warning"
            },
            {
                "label": "Placed Today",
                "value": 0,
                "status": "healthy"
            }
        ],
        "updatedAt": now
    }

# ── POST /po/drafts/:id/place ──────────────────────────────────────
@app.post("/api/po/drafts/{po_id}/place")
async def place_po(po_id: str, body: dict = {}):
    await notify_clients("po_drafts")
    return {"ok": True, "po_id": po_id, "status": "placed"}

# ── POST /po/drafts/:id/reject ─────────────────────────────────────
@app.post("/api/po/drafts/{po_id}/reject")
async def reject_po(po_id: str, body: dict = {}):
    await notify_clients("po_drafts")
    return {"ok": True, "po_id": po_id, "status": "rejected"}

# ── POST /po/drafts/:id/snooze ─────────────────────────────────────
@app.post("/api/po/drafts/{po_id}/snooze")
async def snooze_po(po_id: str, body: dict = {}):
    return {"ok": True, "po_id": po_id, "status": "snoozed"}

# ── POST /api/chat ─────────────────────────────────────────────────
@app.post("/api/chat")
async def chat(request: dict):
    try:
        import sys
        sys.path.append(os.path.dirname(__file__))
        from agents.orchestrator import run_ai_orchestrator

        messages = request.get("messages", [])

        # Keep only last 6 messages to avoid context overflow
        recent_messages = messages[-6:] if len(messages) > 6 else messages

        # Build conversation history string
        history = ""
        if len(recent_messages) > 1:
            for msg in recent_messages[:-1]:  # all except current
                role = "User" if msg["role"] == "user" else "Assistant"
                history += f"{role}: {msg['content']}\n"

        # Current question
        question = recent_messages[-1]["content"] if recent_messages else ""

        # Combine history with current question
        if history:
            full_context = f"""Previous conversation:
            {history}
            Current question: {question}

            Answer the current question. Use the conversation history for context if the question refers to something previously discussed."""
        else:
            full_context = question

        answer, agents_used = run_ai_orchestrator(full_context)
        return {"reply": answer, "agents": agents_used}

    except Exception as e:
        return {"reply": f"Error: {str(e)}", "agents": []}

# ── WebSocket ──────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(ws)

@app.post("/api/notify-refresh")
async def notify_refresh(request: dict):
    topic = request.get("topic", "all")
    await notify_clients(topic)
    return {"notified": len(connected_clients)}

async def notify_clients(topic: str):
    disconnected = []
    for client in connected_clients:
        try:
            await client.send_text(json.dumps({"type": topic}))
        except:
            disconnected.append(client)
    for client in disconnected:
        connected_clients.remove(client)

# ── Health check ───────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Supply Chain API running"}

@app.get("/api/forecasts")
def forecasts():
    
    # At risk SKUs
    at_risk = pd.read_sql("""
        SELECT sku_id, zone_id, product_name, city,
               current_stock, forecasted_demand,
               ROUND((current_stock - forecasted_demand * 14)::numeric, 0) AS stock_gap,
               upper_bound, lower_bound, status
        FROM inventory_summary
        WHERE current_stock < forecasted_demand * 14
        ORDER BY stock_gap ASC
        LIMIT 20
    """, get_engine())

    # Zone level forecast summary
    zone_forecast = pd.read_sql("""
        SELECT city,
               SUM(forecasted_demand)                              AS total_demand,
               COUNT(CASE WHEN current_stock < forecasted_demand * 14 
                     THEN 1 END)                                   AS skus_at_risk,
               ROUND(AVG(upper_bound - lower_bound)::numeric, 1)  AS avg_uncertainty
        FROM inventory_summary
        GROUP BY city
        ORDER BY skus_at_risk DESC
    """, get_engine())

    total_at_risk = len(at_risk)
    total_demand  = int(at_risk["forecasted_demand"].sum() * 14)

    kpis = [
        {
            "label": "SKUs at Risk (2 weeks)",
            "value": total_at_risk,
            "status": "critical" if total_at_risk > 50 else "warning"
        },
        {
            "label": "Total 2-Week Demand",
            "value": f"{total_demand:,}",
            "status": "healthy"
        },
        {
            "label": "Zones with Risk",
            "value": int(zone_forecast[zone_forecast["skus_at_risk"] > 0].shape[0]),
            "status": "warning"
        },
        {
            "label": "Highest Risk Zone",
            "value": zone_forecast.iloc[0]["city"] if len(zone_forecast) > 0 else "None",
            "status": "critical"
        }
    ]

    at_risk["stock_gap"] = at_risk["stock_gap"].fillna(0)

    return {
        "kpis": kpis,
        "atRisk": at_risk.to_dict(orient="records"),
        "byZone": zone_forecast.to_dict(orient="records"),
        "updatedAt": datetime.now().isoformat()
    }