import streamlit as st
import sys, os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

sys.path.append(os.path.dirname(__file__))

st.set_page_config(
    page_title="Supply Chain Intelligence",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── color palette ──────────────────────────────────────────────────
BG     = "#0d1117"
CARD   = "#161b22"
BORDER = "#30363d"
CREAM  = "#e6d9c0"
MUTED  = "#8b949e"
RED    = "#f85149"
AMBER  = "#d29922"
GREEN  = "#3fb950"
BLUE   = "#58a6ff"
ACCENT = "#1f6feb"
BG     = "#0d1420"
CARD   = "#1a2744"
BORDER = "#2a3f6f"

st.markdown(f"""
<style>
            
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

*, html, body, [class*="css"] {{
    font-family: 'IBM Plex Sans', sans-serif !important;
    box-sizing: border-box;
}}
.stApp {{ background: {BG} !important; }}
.block-container {{ padding: 1.5rem 2rem 3rem 2rem !important; max-width: 100% !important; }}
[data-testid="stHeader"] {{ background: {BG} !important; }}
[data-testid="stSidebar"] {{ background: {CARD} !important; }}
section[data-testid="stSidebar"] * {{ color: {CREAM} !important; }}
[data-testid="collapsedControl"] {{ display: none !important; }}
[data-testid="stSelectbox"] > div > div {{
    background: {CARD} !important; border: 1px solid {BORDER} !important;
    border-radius: 8px !important; color: {CREAM} !important;
}}
span[data-testid="stIconMaterial"] {{ display: none !important; }}
button[data-testid="collapsedControl"] {{ display: none !important; }}
[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
.stButton > button {{
    background: {CARD} !important; color: {CREAM} !important;
    border: 1px solid {BORDER} !important; border-radius: 8px !important;
    font-size: 12px !important; width: 100%;
}}
.stButton > button:hover {{ border-color: {CREAM} !important; background: #1c2128 !important; }}

[data-testid="stChatInput"] textarea {{
    background: {CARD} !important; color: {CREAM} !important;
    border: 1px solid {BORDER} !important; border-radius: 8px !important;
}}

[data-testid="stSelectbox"] {{ margin-top: 12px !important; }}

[data-testid="stSelectbox"] > div {{ cursor: pointer !important; }}
[data-testid="stSelectbox"] select {{ cursor: pointer !important; }}

[data-testid="collapsedControl"] {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 6px !important;
    color: {CREAM} !important;
}}
[data-testid="collapsedControl"] svg {{ fill: {CREAM} !important; }}

[data-testid="collapsedControl"] svg path {{ fill: {CREAM} !important; }}
[data-testid="stSidebarCollapsedControl"] {{ background: {CARD} !important; border-right: 1px solid {BORDER} !important; }}

::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 4px; }}

.page-title {{ font-size: 20px; font-weight: 600; color: {CREAM}; letter-spacing: -0.3px; margin: 0; }}
.page-sub   {{ font-size: 12px; color: {MUTED}; margin: 3px 0 0 0; }}
.live-dot   {{ display: inline-block; width: 7px; height: 7px; background: {GREEN}; border-radius: 50%; margin-right: 5px; vertical-align: middle; }}
.sec-lbl    {{ font-size: 10px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: {MUTED}; margin: 0 0 10px 0; }}
.divider    {{ border: none; border-top: 1px solid {BORDER}; margin: 1rem 0; }}

.kpi-box    {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 16px 18px; position: relative; overflow: hidden; }}
.kpi-bar    {{ position: absolute; top: 0; left: 0; right: 0; height: 2px; }}
.kpi-lbl    {{ font-size: 11px; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}
.kpi-val    {{ font-size: 30px; font-weight: 600; color: {CREAM}; font-family: 'IBM Plex Mono', monospace; line-height: 1; margin-bottom: 4px; }}
.note-red   {{ font-size: 12px; color: {RED}; }}
.note-amber {{ font-size: 12px; color: {AMBER}; }}
.note-green {{ font-size: 12px; color: {GREEN}; }}
.note-blue  {{ font-size: 12px; color: {BLUE}; }}

.chart-box  {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 16px 18px 8px 18px; }}
.chart-lbl  {{ font-size: 11px; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.7px; margin-bottom: 10px; }}

.chat-wrap  {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 14px; }}
.msg-user   {{ background: {ACCENT}; color: #fff; padding: 8px 12px; border-radius: 10px 10px 2px 10px; font-size: 13px; margin: 6px 0 6px 25%; line-height: 1.5; }}
.msg-ai     {{ background: #1c2128; border: 1px solid {BORDER}; color: {CREAM}; padding: 8px 12px; border-radius: 10px 10px 10px 2px; font-size: 13px; margin: 4px 25% 2px 0; line-height: 1.5; white-space: pre-wrap; }}
.msg-tag    {{ font-size: 10px; color: #484f58; font-family: 'IBM Plex Mono', monospace; margin: 0 0 6px 0; }}
</style>
""", unsafe_allow_html=True)

# ── helpers ────────────────────────────────────────────────────────
def base_layout(h=260, margin=None):
    m = margin or dict(l=10, r=20, t=10, b=10)
    return dict(
        height=h, margin=m,
        paper_bgcolor=CARD, plot_bgcolor=CARD,
        font=dict(family="IBM Plex Sans", size=12, color=CREAM),
        xaxis=dict(gridcolor=BORDER, color=MUTED, showline=False, zeroline=False),
        yaxis=dict(gridcolor=BORDER, color=MUTED, showline=False, zeroline=False),
        legend=dict(orientation="h", y=-0.3, x=0, font_size=11, font_color=MUTED),
    )

ZONE_MAP    = {"All Zones":None,"Zone A — Los Angeles":["A"],"Zone B — Chicago":["B"],"Zone C — Dallas":["C"],"Zone D — New York":["D"],"Zone E — Atlanta":["E"]}
ZONE_LABELS = {"A":"Los Angeles","B":"Chicago","C":"Dallas","D":"New York","E":"Atlanta"}
AGENT_NAMES = {"get_warehouse_status":"Warehouse","get_transport_status":"Transport","get_shipment_status":"Shipments","get_sales_status":"Sales","get_forecast_status":"Forecast"}

if "messages"   not in st.session_state: st.session_state.messages   = []
if "agents_log" not in st.session_state: st.session_state.agents_log = []

# ── header ─────────────────────────────────────────────────────────
h1, h2 = st.columns([5,2])
with h1:
    st.title("Supply Chain Intelligence")
with h2:
    selected_zone = st.selectbox("Zone", list(ZONE_MAP.keys()), label_visibility="collapsed")

zone_ids = ZONE_MAP[selected_zone]
zone_key = tuple(zone_ids) if zone_ids else ("ALL",)
st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ── data loaders ───────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def load_warehouse(zk):
    from agents.warehouse_agent import get_warehouse_stats, get_atp
    z = None if zk == ("ALL",) else list(zk)
    stats, critical, warning, healthy, df = get_warehouse_stats(z)
    atp_df  = get_atp(z)
    at_risk = atp_df[atp_df["stockout_prediction"] != "Beyond 3 weeks"]
    return stats, critical, warning, healthy, df, at_risk

@st.cache_data(ttl=60, show_spinner=False)
def load_transport(zk):
    from agents.transport_agent import get_transport_stats
    z = None if zk == ("ALL",) else list(zk)
    stats, df, delayed, expensive, poor, carrier_summary, best = get_transport_stats(z)
    return stats, df, carrier_summary

@st.cache_data(ttl=60, show_spinner=False)
def load_shipment(zk):
    from agents.shipment_agent import get_shipment_stats
    z = None if zk == ("ALL",) else list(zk)
    stats, df, delayed, held, lost, in_transit, pod = get_shipment_stats(z)
    return stats, delayed

@st.cache_data(ttl=60, show_spinner=False)
def load_forecast(zk):
    from agents.forecast_agent import get_forecast_stats
    z = None if zk == ("ALL",) else list(zk)
    stats, df, at_risk = get_forecast_stats(z)
    return stats, at_risk

with st.spinner("Loading supply chain data..."):
    try:
        wh_stats, crit_df, warn_df, hlth_df, inv_df, atp_risk = load_warehouse(zone_key)
        tr_stats, tr_df, carrier_df                            = load_transport(zone_key)
        sh_stats, del_df                                       = load_shipment(zone_key)
        fc_stats, fc_risk                                      = load_forecast(zone_key)
        ok = True
    except Exception as e:
        import traceback
        st.error(f"Data load error: {str(e)}")
        st.code(traceback.format_exc())
        ok = False

if not ok:
    st.stop()

# ══════════════════════════════════════════════════════════════════
# KPI ROW
# ══════════════════════════════════════════════════════════════════
st.markdown("<p class='sec-lbl'>Key Metrics</p>", unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"<div class='kpi-box'><div class='kpi-bar' style='background:{RED}'></div><div class='kpi-lbl'>Critical SKUs</div><div class='kpi-val'>{wh_stats['critical_count']}</div><div class='note-red'>Immediate reorder needed</div></div>", unsafe_allow_html=True)
with k2:
    vr = sh_stats.get('value_at_risk', 0)
    st.markdown(f"<div class='kpi-box'><div class='kpi-bar' style='background:{AMBER}'></div><div class='kpi-lbl'>Delayed Shipments</div><div class='kpi-val'>{sh_stats['delayed']}</div><div class='note-amber'>Value at risk: ${vr:,.0f}</div></div>", unsafe_allow_html=True)
with k3:
    ot  = tr_stats['on_time_pct']
    col = GREEN if ot >= 75 else AMBER if ot >= 50 else RED
    cls = "green" if ot >= 75 else "amber" if ot >= 50 else "red"
    st.markdown(f"<div class='kpi-box'><div class='kpi-bar' style='background:{col}'></div><div class='kpi-lbl'>On-Time Delivery</div><div class='kpi-val'>{ot:.0f}%</div><div class='note-{cls}'>Worst: {tr_stats['worst_carrier']}</div></div>", unsafe_allow_html=True)
with k4:
    st.markdown(f"<div class='kpi-box'><div class='kpi-bar' style='background:{BLUE}'></div><div class='kpi-lbl'>2-Week Stockout Risk</div><div class='kpi-val'>{fc_stats['skus_at_risk_2weeks']}</div><div class='note-blue'>{fc_stats['total_2week_demand']:,} units demand</div></div>", unsafe_allow_html=True)

st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# CHARTS ROW 1
# ══════════════════════════════════════════════════════════════════
st.markdown("<p class='sec-lbl'>Performance Overview</p>", unsafe_allow_html=True)
c1, c2 = st.columns(2)

with c1:
    st.markdown("<div class='chart-box'><p class='chart-lbl'>Inventory health by zone</p>", unsafe_allow_html=True)
    if not inv_df.empty and "zone_id" in inv_df.columns and "status" in inv_df.columns:
        zh = inv_df.groupby(["zone_id","status"]).size().reset_index(name="count")
        zh["zone_name"] = zh["zone_id"].map(ZONE_LABELS).fillna(zh["zone_id"])
        cmap = {"CRITICAL":RED,"WARNING":AMBER,"HEALTHY":GREEN,"Critical":RED,"Warning":AMBER,"Healthy":GREEN}
        fig1 = px.bar(zh, x="zone_name", y="count", color="status", color_discrete_map=cmap,
                      barmode="stack", labels={"zone_name":"","count":"SKUs","status":""})
        fig1.update_layout(**base_layout(240))
        fig1.update_traces(marker_line_width=0)
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar":False})
    else:
        st.markdown(f"<p style='color:{MUTED};font-size:13px;padding:20px 0'>No zone inventory data.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='chart-box'><p class='chart-lbl'>Carrier performance score</p>", unsafe_allow_html=True)
    if not carrier_df.empty and "avg_perf_score" in carrier_df.columns:
        cs = carrier_df.sort_values("avg_perf_score", ascending=True).head(8)
        bcolors = [RED if s < 50 else AMBER if s < 70 else GREEN for s in cs["avg_perf_score"]]
        fig2 = go.Figure(go.Bar(
            x=cs["avg_perf_score"], y=cs["carrier"], orientation="h",
            marker_color=bcolors, marker_line_width=0,
            text=[f"{v:.1f}" for v in cs["avg_perf_score"]],
            textposition="outside", textfont=dict(color=CREAM, size=11)
        ))
        l2 = base_layout(240, dict(l=10,r=50,t=10,b=10))
        l2["xaxis"].update(range=[0,110], title=None)
        l2["yaxis"]["title"] = None
        fig2.update_layout(**l2)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
    else:
        st.markdown(f"<p style='color:{MUTED};font-size:13px;padding:20px 0'>No carrier data.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# CHARTS ROW 2
# ══════════════════════════════════════════════════════════════════
st.markdown("<p class='sec-lbl'>Forecast & Shipment Risk</p>", unsafe_allow_html=True)
c3, c4 = st.columns(2)

with c3:
    st.markdown("<div class='chart-box'><p class='chart-lbl'>Stockout risk by zone (2-week)</p>", unsafe_allow_html=True)
    if not fc_risk.empty and "zone_id" in fc_risk.columns:
        fz = fc_risk.groupby("zone_id").size().reset_index(name="at_risk")
        fz["zone_name"] = fz["zone_id"].map(ZONE_LABELS).fillna(fz["zone_id"])
        fig3 = go.Figure(go.Bar(
            x=fz["zone_name"], y=fz["at_risk"],
            marker_color=AMBER, marker_line_width=0,
            text=fz["at_risk"], textposition="outside",
            textfont=dict(color=CREAM, size=11)
        ))
        l3 = base_layout(230)
        l3["yaxis"]["title"] = "SKUs at risk"
        fig3.update_layout(**l3)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})
    else:
        st.markdown(f"<p style='color:{MUTED};font-size:13px;padding:20px 0'>No forecast risk data.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown("<div class='chart-box'><p class='chart-lbl'>Shipment status breakdown</p>", unsafe_allow_html=True)
    labels = ["In Transit","Delayed","Held at Hub","Lost"]
    values = [sh_stats.get("in_transit",0), sh_stats.get("delayed",0),
              sh_stats.get("held_at_hub",0), sh_stats.get("lost_in_transit",0)]
    if sum(values) > 0:
        fig4 = go.Figure(go.Pie(
            labels=labels, values=values,
            marker=dict(colors=[BLUE,AMBER,RED,"#6e40c9"], line=dict(color=CARD,width=2)),
            textfont=dict(color=CREAM, size=12),
            hole=0.45, textinfo="label+percent"
        ))
        l4 = base_layout(230)
        l4["showlegend"] = False
        fig4.update_layout(**l4)
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar":False})
    else:
        st.markdown(f"<p style='color:{MUTED};font-size:13px;padding:20px 0'>No shipment data.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# BOTTOM — table + chat
# ══════════════════════════════════════════════════════════════════
st.markdown("<p class='sec-lbl'>Critical SKUs & AI Assistant</p>", unsafe_allow_html=True)
t1, t2 = st.columns([1.4, 1])

with t1:
    st.markdown("<div class='chart-box'><p class='chart-lbl'>Critical SKUs — immediate action required</p>", unsafe_allow_html=True)
    if not crit_df.empty:
        show = [c for c in ["sku_id","zone_id","product_name","category","current_stock","days_of_stock","action_required","supplier"] if c in crit_df.columns]
        tbl  = crit_df[show].head(12).copy()
        tbl.columns = [c.replace("_"," ").title() for c in tbl.columns]
        st.dataframe(tbl, use_container_width=True, hide_index=True, height=380,
                     column_config={"Days Of Stock": st.column_config.NumberColumn(format="%.1f d"),
                                    "Current Stock": st.column_config.NumberColumn(format="%d")})
    else:
        st.markdown(f"<p style='color:{MUTED};font-size:13px'>No critical SKUs.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with t2:
    st.markdown("<div class='chat-wrap'><p class='chart-lbl'>AI Assistant</p>", unsafe_allow_html=True)

    chat_box = st.container(height=300)
    with chat_box:
        if not st.session_state.messages:
            st.markdown(f"<p style='color:{MUTED};font-size:13px;margin-top:8px'>Ask anything about your supply chain.</p>", unsafe_allow_html=True)
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                st.markdown(f"<div class='msg-user'>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='msg-ai'>{msg['content']}</div>", unsafe_allow_html=True)
                idx = i // 2
                if idx < len(st.session_state.agents_log) and st.session_state.agents_log[idx]:
                    friendly = [AGENT_NAMES.get(a,a) for a in st.session_state.agents_log[idx]]
                    st.markdown(f"<div class='msg-tag'>via {' · '.join(friendly)}</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
    qc1, qc2 = st.columns(2)
    with qc1:
        if st.button("Critical in Chicago?",    key="q1", use_container_width=True): st.session_state.pending_q = "Which SKUs are critical in Chicago?"
        if st.button("Dallas stockout risk?",   key="q3", use_container_width=True): st.session_state.pending_q = "Will we run out of stock next week in Dallas?"
    with qc2:
        if st.button("Worst carrier?",          key="q2", use_container_width=True): st.session_state.pending_q = "Which carrier is performing worst?"
        if st.button("Overall health summary?", key="q4", use_container_width=True): st.session_state.pending_q = "Give me an overall supply chain health summary"

    prompt = st.chat_input("Ask about your supply chain...")
    if "pending_q" in st.session_state:
        prompt = st.session_state.pending_q
        del st.session_state.pending_q

    st.markdown("</div>", unsafe_allow_html=True)

    if prompt:
        st.session_state.messages.append({"role":"user","content":prompt})
        with st.spinner("Thinking..."):
            try:
                from agents.orchestrator import run_ai_orchestrator
                answer, agents_used = run_ai_orchestrator(prompt)
                st.session_state.messages.append({"role":"assistant","content":answer})
                st.session_state.agents_log.append(agents_used)
            except Exception as e:
                answer = f"Error: {str(e)}"
                st.session_state.messages.append({"role":"assistant","content":answer})
                st.session_state.agents_log.append([])
        st.rerun()

# ── sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<p style='font-size:14px;font-weight:600;color:{CREAM}'>Session Stats</p>", unsafe_allow_html=True)
    st.metric("Questions asked", len(st.session_state.messages) // 2)
    st.metric("Warning SKUs",    wh_stats.get("warning_count", 0))
    st.metric("Healthy SKUs",    wh_stats.get("healthy_count", 0))
    st.metric("Total SKUs",      wh_stats.get("total_skus", 0))
    st.divider()
    if st.button("Clear chat history"):
        st.session_state.messages   = []
        st.session_state.agents_log = []
        st.rerun()