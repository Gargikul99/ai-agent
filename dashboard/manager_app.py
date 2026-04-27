"""
Manager Supply Chain Dashboard
Single chat UI covering Warehouse + Transport + Shipment
Run with: streamlit run manager_app.py
"""

import streamlit as st
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

from calculations import load_and_calculate, get_summary_stats, get_display_cols_critical, get_display_cols_warning
from transport_agent import get_transport_context
from shipment_agent import get_shipment_context
from orchestrator import route_question, build_combined_context

WH_FILE = "fmcg_warehouse_inventory.xlsx"
TR_FILE = "transport_data.xlsx"
SH_FILE = "shipment_data.xlsx"

st.set_page_config(page_title="Supply Chain Command", page_icon="🏭", layout="wide")

st.markdown("""
<style>
.metric-card{background:var(--color-background-secondary);border-radius:10px;padding:14px 16px;text-align:center;border:0.5px solid var(--color-border-tertiary)}
.metric-val{font-size:24px;font-weight:600;margin:0;color:var(--color-text-primary)}
.metric-lbl{font-size:11px;color:var(--color-text-secondary);margin:4px 0 0}
.critical{color:#c62828!important}.warning{color:#f9a825!important}
.healthy{color:#2e7d32!important}.info{color:#1565c0!important}
.chat-user{background:#e3f2fd;border-radius:12px 12px 2px 12px;padding:10px 14px;margin:6px 0;max-width:80%;margin-left:auto;font-size:14px;color:#1a237e}
.chat-agent{background:#f1f8e9;border-radius:12px 12px 12px 2px;padding:10px 14px;margin:6px 0;max-width:88%;font-size:14px;line-height:1.7;color:#1b5e20}
.agent-badge{display:inline-block;font-size:11px;padding:2px 8px;border-radius:20px;margin-right:4px;font-weight:500}
.wh-badge{background:#E1F5EE;color:#085041}
.tr-badge{background:#FAEEDA;color:#633806}
.sh-badge{background:#E6F1FB;color:#0C447C}
.section-hdr{font-size:12px;font-weight:600;color:var(--color-text-secondary);text-transform:uppercase;letter-spacing:0.5px;margin:14px 0 6px}
</style>
""", unsafe_allow_html=True)

# ── Load all data ────────────────────────────────────────────
@st.cache_data
def load_all():
    wh_df, wh_crit, wh_warn, wh_heal = load_and_calculate(WH_FILE)
    wh_stats = get_summary_stats(wh_df, wh_crit, wh_warn, wh_heal)
    tr_stats, tr_delayed, tr_poor, tr_summ = get_transport_context(TR_FILE)
    sh_stats, sh_delayed, sh_held, sh_lost = get_shipment_context(SH_FILE)
    return (wh_df, wh_crit, wh_warn, wh_heal, wh_stats,
            tr_stats, tr_delayed, tr_poor, tr_summ,
            sh_stats, sh_delayed, sh_held, sh_lost)

@st.cache_resource
def load_llm():
    return OllamaLLM(model="gemma4:e2b")

prompt_template = PromptTemplate.from_template("""
You are a supply chain intelligence system reporting to a senior manager.
All numbers below are Python-calculated and accurate. Do NOT recalculate.
Your job: explain, interpret, and recommend actions clearly and concisely.

Agents consulted: {agents_used}

{combined_context}

Manager's question: {question}

Respond like a professional supply chain analyst briefing a manager.
Be specific — use SKU names, carrier names, shipment IDs, and numbers.
End with 1-2 clear recommended actions if relevant.
""")

(wh_df, wh_crit, wh_warn, wh_heal, wh_stats,
 tr_stats, tr_delayed, tr_poor, tr_summ,
 sh_stats, sh_delayed, sh_held, sh_lost) = load_all()
llm = load_llm()

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏭 Supply Chain Command")
    st.markdown("---")

    # Warehouse metrics
    st.markdown('<p class="section-hdr">Warehouse</p>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p class="metric-val critical">{wh_stats["critical_count"]}</p><p class="metric-lbl">Critical</p></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p class="metric-val warning">{wh_stats["warning_count"]}</p><p class="metric-lbl">Warning</p></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p class="metric-val healthy">{wh_stats["healthy_count"]}</p><p class="metric-lbl">Healthy</p></div>', unsafe_allow_html=True)

    # Transport metrics
    st.markdown('<p class="section-hdr">Transport</p>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1: st.markdown(f'<div class="metric-card"><p class="metric-val info">{tr_stats["on_time_pct"]}%</p><p class="metric-lbl">On Time</p></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p class="metric-val warning">{tr_stats["delayed_lanes"]}</p><p class="metric-lbl">Delayed Lanes</p></div>', unsafe_allow_html=True)

    # Shipment metrics
    st.markdown('<p class="section-hdr">Shipments</p>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><p class="metric-val info">{sh_stats["in_transit"]}</p><p class="metric-lbl">In Transit</p></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><p class="metric-val warning">{sh_stats["delayed"]}</p><p class="metric-lbl">Delayed</p></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><p class="metric-val critical">{sh_stats["lost_in_transit"]}</p><p class="metric-lbl">Lost</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p class="section-hdr">Suggested questions</p>', unsafe_allow_html=True)
    suggestions = [
        "Give me an overall supply chain health summary",
        "Which SKUs need immediate restocking?",
        "Which carrier is performing worst?",
        "How many shipments are delayed right now?",
        "Why might fulfilment be suffering this week?",
        "What are the top 3 actions I should take today?",
        "Which customer is most affected by delays?",
        "What is the total value of shipments at risk?",
    ]
    for s in suggestions:
        if st.button(s, use_container_width=True, key=s):
            st.session_state.pending = s

# ── Main area ────────────────────────────────────────────────
st.markdown("## 🏭 Supply Chain Command Centre")
st.markdown("*Warehouse · Transport · Shipment — one view for the manager*")

# Top KPI row
cols = st.columns(6)
kpis = [
    (wh_stats["total_skus"],          "Total SKUs",       "info"),
    (wh_stats["critical_count"],      "Critical Stock",   "critical"),
    (f"{tr_stats['on_time_pct']}%",   "On-Time Delivery", "healthy"),
    (tr_stats["delayed_lanes"],       "Delayed Lanes",    "warning"),
    (sh_stats["delayed"],             "Delayed Shipments","warning"),
    (sh_stats["lost_in_transit"],     "Lost Shipments",   "critical"),
]
for col,(val,lbl,cls) in zip(cols,kpis):
    with col:
        st.markdown(f'<div class="metric-card"><p class="metric-val {cls}">{val}</p><p class="metric-lbl">{lbl}</p></div>', unsafe_allow_html=True)

st.markdown("---")

# Data expanders
with st.expander("📦 Warehouse — critical & warning SKUs"):
    t1,t2 = st.tabs(["Critical","Warning"])
    with t1: st.dataframe(wh_crit[get_display_cols_critical()], use_container_width=True)
    with t2: st.dataframe(wh_warn[get_display_cols_warning()], use_container_width=True)

with st.expander("🚛 Transport — delayed & poor-performing lanes"):
    t1,t2,t3 = st.tabs(["Delayed Lanes","Poor Performers","Carrier Summary"])
    with t1: st.dataframe(tr_delayed, use_container_width=True)
    with t2: st.dataframe(tr_poor, use_container_width=True)
    with t3: st.dataframe(tr_summ, use_container_width=True)

with st.expander("📬 Shipments — delayed, held & lost"):
    t1,t2,t3 = st.tabs(["Delayed","Held at Hub","Lost in Transit"])
    with t1: st.dataframe(sh_delayed, use_container_width=True)
    with t2: st.dataframe(sh_held, use_container_width=True)
    with t3: st.dataframe(sh_lost, use_container_width=True)

st.markdown("---")
st.markdown("#### Ask anything about your supply chain")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    css = "chat-user" if msg["role"]=="user" else "chat-agent"
    icon = "🧑" if msg["role"]=="user" else "🤖"
    badges = ""
    if msg["role"]=="assistant" and "agents" in msg:
        for a in msg["agents"]:
            cls = {"Warehouse":"wh","Transport":"tr","Shipment":"sh"}.get(a,"wh")
            badges += f'<span class="agent-badge {cls}-badge">{a}</span>'
        badges = f'<div style="margin-bottom:6px">{badges}</div>'
    st.markdown(f'<div class="{css}">{icon} {badges}{msg["content"]}</div>', unsafe_allow_html=True)

if "pending" in st.session_state:
    question = st.session_state.pop("pending")
else:
    question = None

user_input = st.chat_input("Ask about warehouse, transport, or shipments...")
if user_input:
    question = user_input

if question:
    st.markdown(f'<div class="chat-user">🧑 {question}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role":"user","content":question})

    routing = route_question(question)
    # fallback if nothing matched — use all
    if not any(routing.values()):
        routing = {"warehouse":True,"transport":True,"shipment":True}

    combined_context, agents_used = build_combined_context(
        question, routing,
        wh_stats=wh_stats,
        wh_critical=wh_crit[get_display_cols_critical()],
        wh_warning=wh_warn[get_display_cols_warning()],
        tr_stats=tr_stats, tr_delayed=tr_delayed, tr_poor=tr_poor, tr_summ=tr_summ,
        sh_stats=sh_stats, sh_delayed=sh_delayed, sh_held=sh_held, sh_lost=sh_lost,
    )

    with st.spinner(f"Consulting {', '.join(agents_used)} agent{'s' if len(agents_used)>1 else ''}..."):
        final_prompt = prompt_template.format(
            agents_used     = ", ".join(agents_used),
            combined_context= combined_context,
            question        = question,
        )
        answer = llm.invoke(final_prompt)

    cls_map = {"Warehouse": "wh", "Transport": "tr", "Shipment": "sh"}
    badges_html = "".join([
    f'<span class="agent-badge {cls_map.get(a, "wh")}-badge">{a}</span>'
    for a in agents_used
    ])
    st.markdown(f'<div class="chat-agent">🤖 <div style="margin-bottom:6px">{badges_html}</div>{answer}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role":"assistant","content":answer,"agents":agents_used})

if st.session_state.messages:
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()
