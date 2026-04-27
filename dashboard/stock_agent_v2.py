"""
Level 1 Stock Agent v2 — Streamlit UI
Python handles all calculations. Gemma 4 handles explanation only.
Run with: streamlit run stock_agent_v2.py
"""

import streamlit as st
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from calculations import load_and_calculate, get_summary_stats, get_display_cols_critical, get_display_cols_warning

EXCEL_FILE = "fmcg_warehouse_inventory.xlsx"

st.set_page_config(page_title="Warehouse Stock Agent", page_icon="📦", layout="wide")

st.markdown("""
<style>
.metric-card{background:#f8f9fa;border-radius:10px;padding:16px 20px;text-align:center;border:1px solid #e0e0e0}
.metric-val{font-size:28px;font-weight:600;margin:0}
.metric-lbl{font-size:12px;color:#666;margin:4px 0 0}
.critical{color:#c62828}.warning{color:#f9a825}.healthy{color:#2e7d32}.info{color:#1565c0}
.chat-bubble-user{background:#e3f2fd;border-radius:12px 12px 2px 12px;padding:10px 14px;margin:6px 0;max-width:80%;margin-left:auto;font-size:14px;color:#1a237e}
.chat-bubble-agent{background:#f1f8e9;border-radius:12px 12px 12px 2px;padding:10px 14px;margin:6px 0;max-width:85%;font-size:14px;line-height:1.6;color:#1b5e20}
.calc-badge{background:#e8f5e9;color:#2e7d32;font-size:11px;padding:2px 8px;border-radius:20px;font-weight:600}
.section-header{font-size:13px;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:0.5px;margin:16px 0 8px}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return load_and_calculate(EXCEL_FILE)

@st.cache_resource
def load_llm():
    return OllamaLLM(model="gemma4:e2b")

prompt = PromptTemplate.from_template("""
You are a warehouse analyst. All numbers below are pre-calculated by Python — they are accurate.
Your job is to explain, interpret, and recommend actions based on these facts.
Do NOT recalculate anything — just reason about the numbers given.

WAREHOUSE SNAPSHOT (Python-calculated):
- Total SKUs: {total_skus}
- Critical: {critical_count} SKUs ({critical_pct}% of total)
- Warning: {warning_count} SKUs
- Healthy: {healthy_count} SKUs
- Most urgent item: {most_urgent_sku} ({most_urgent_days} days of stock left)
- Categories at risk: {categories_at_risk}
- Total reorder quantity needed: {total_reorder_qty} units

CRITICAL SKUs (Python-calculated, sorted by urgency):
{critical_data}

WARNING SKUs:
{warning_data}

Question: {question}

Answer like a professional supply chain analyst. Use the specific numbers above.
""")

df, critical_skus, warning_skus, healthy_skus = load_data()
stats = get_summary_stats(df, critical_skus, warning_skus, healthy_skus)
llm   = load_llm()

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📦 Warehouse Agent")
    st.markdown('<span class="calc-badge">✓ Python-calculated</span>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<p class="section-header">Stock Health</p>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><p class="metric-val critical">{stats["critical_count"]}</p><p class="metric-lbl">Critical</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><p class="metric-val warning">{stats["warning_count"]}</p><p class="metric-lbl">Warning</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><p class="metric-val healthy">{stats["healthy_count"]}</p><p class="metric-lbl">Healthy</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p class="section-header">Key Numbers</p>', unsafe_allow_html=True)
    st.markdown(f"**Most urgent:** {stats['most_urgent_sku']}")
    st.markdown(f"**Days left:** {stats['most_urgent_days']} days")
    st.markdown(f"**Total reorder qty:** {stats['total_reorder_qty']:,} units")
    st.markdown(f"**Categories at risk:** {stats['categories_at_risk']}")

    st.markdown("---")
    st.markdown('<p class="section-header">Critical SKUs</p>', unsafe_allow_html=True)
    for _, row in critical_skus[["Product Name","Days of Stock Left","Action Required"]].iterrows():
        color = "🔴" if "NOW" in row["Action Required"] else "🟠"
        st.markdown(f"{color} **{row['Product Name']}** — {row['Days of Stock Left']} days")

    st.markdown("---")
    st.markdown('<p class="section-header">Suggested Questions</p>', unsafe_allow_html=True)
    suggestions = [
        "Which SKUs need immediate restocking?",
        "Which category is most at risk?",
        "Which items run out within 3 days?",
        "Summarise the warehouse health",
        "Which supplier has the most critical items?",
        "What is the total reorder quantity needed?",
    ]
    for s in suggestions:
        if st.button(s, use_container_width=True, key=s):
            st.session_state.pending_question = s

# ── Main area ──────────────────────────────────────────────
st.markdown("## 📦 FMCG Warehouse Stock Agent")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><p class="metric-val info">{stats["total_skus"]}</p><p class="metric-lbl">Total SKUs</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><p class="metric-val critical">{stats["critical_count"]}</p><p class="metric-lbl">Critical</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><p class="metric-val warning">{stats["warning_count"]}</p><p class="metric-lbl">Warning</p></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><p class="metric-val healthy">{stats["healthy_count"]}</p><p class="metric-lbl">Healthy</p></div>', unsafe_allow_html=True)

st.markdown("---")

with st.expander("📊 View Python-calculated data table"):
    tab1, tab2 = st.tabs(["🔴 Critical SKUs", "🟡 Warning SKUs"])
    with tab1:
        st.dataframe(critical_skus[get_display_cols_critical()], use_container_width=True)
    with tab2:
        st.dataframe(warning_skus[get_display_cols_warning()], use_container_width=True)

st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-bubble-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-bubble-agent">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")
else:
    question = None

user_input = st.chat_input("Ask about your inventory...")
if user_input:
    question = user_input

if question:
    st.markdown(f'<div class="chat-bubble-user">🧑 {question}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": question})

    with st.spinner("Agent thinking..."):
        context = prompt.format(
            **stats,
            critical_data = critical_skus[get_display_cols_critical()].to_string(index=False),
            warning_data  = warning_skus[get_display_cols_warning()].to_string(index=False),
            question      = question,
        )
        answer = llm.invoke(context)

    st.markdown(f'<div class="chat-bubble-agent">🤖 {answer}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": answer})

if st.session_state.messages:
    if st.button("🗑 Clear chat"):
        st.session_state.messages = []
        st.rerun()
