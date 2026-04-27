"""
FMCG Warehouse Stock Agent — Streamlit UI
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

st.set_page_config(page_title="Warehouse Stock Agent", page_icon="📦", layout="wide")

st.markdown("""
<style>
.metric-card {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
    border: 1px solid #e0e0e0;
}
.metric-val { font-size: 28px; font-weight: 600; margin: 0; }
.metric-lbl { font-size: 12px; color: #666; margin: 4px 0 0; }
.critical { color: #c62828; }
.warning  { color: #f9a825; }
.healthy  { color: #2e7d32; }
.chat-bubble-user {
    background: #e3f2fd;
    border-radius: 12px 12px 2px 12px;
    padding: 10px 14px;
    margin: 6px 0;
    max-width: 80%;
    margin-left: auto;
    font-size: 14px;
    color: #1b5e20;
}
.chat-bubble-agent {
    background: #f1f8e9;
    border-radius: 12px 12px 12px 2px;
    padding: 10px 14px;
    margin: 6px 0;
    max-width: 85%;
    font-size: 14px;
    line-height: 1.6;
    color: #1b5e20;
}
.section-header {
    font-size: 13px;
    font-weight: 600;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 16px 0 8px;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_excel("fmcg_warehouse_inventory.xlsx", sheet_name="Inventory Data")
    critical = df[df["Current Stock (Units)"] < df["Reorder Point (Units)"] * 0.5]
    warning  = df[(df["Current Stock (Units)"] >= df["Reorder Point (Units)"] * 0.5) &
                  (df["Current Stock (Units)"] <  df["Reorder Point (Units)"])]
    healthy  = df[df["Current Stock (Units)"] >= df["Reorder Point (Units)"]]
    return df, critical, warning, healthy

@st.cache_resource
def load_llm():
    return OllamaLLM(model="gemma4:e2b")

prompt = PromptTemplate.from_template("""
You are a warehouse analyst. Answer briefly and clearly.

STOCK SUMMARY:
- Total SKUs: {total_skus}
- Critical (act today): {critical_count} SKUs
- Warning (act this week): {warning_count} SKUs
- Healthy: {healthy_count} SKUs

CRITICAL SKUs:
{critical_data}

WARNING SKUs:
{warning_data}

Question: {question}
""")

df, critical_skus, warning_skus, healthy_skus = load_data()
llm = load_llm()

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📦 Warehouse Agent")
    st.markdown("---")
    st.markdown('<p class="section-header">Stock Health</p>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><p class="metric-val critical">{len(critical_skus)}</p><p class="metric-lbl">Critical</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><p class="metric-val warning">{len(warning_skus)}</p><p class="metric-lbl">Warning</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><p class="metric-val healthy">{len(healthy_skus)}</p><p class="metric-lbl">Healthy</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p class="section-header">Critical SKUs</p>', unsafe_allow_html=True)
    for _, row in critical_skus[["Product Name","Days of Stock Left"]].iterrows():
        days = row["Days of Stock Left"]
        st.markdown(f"🔴 **{row['Product Name']}** — {days} days left")

    st.markdown("---")
    st.markdown('<p class="section-header">Suggested Questions</p>', unsafe_allow_html=True)
    suggestions = [
        "Which SKUs need immediate restocking?",
        "Which category is most at risk?",
        "Which items run out within 3 days?",
        "Summarise the warehouse health",
        "Which supplier has the most critical items?",
    ]
    for s in suggestions:
        if st.button(s, use_container_width=True, key=s):
            st.session_state.pending_question = s

# ── Main area ──────────────────────────────────────────────
st.markdown("## 📦 FMCG Warehouse Stock Agent")
st.markdown(f"Analysing **{len(df)} SKUs** across **{df['Category'].nunique()} categories** · Model: `gemma4:e2b`")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-bubble-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-bubble-agent">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

# Handle sidebar button clicks
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")
else:
    question = None

# Chat input
user_input = st.chat_input("Ask about your inventory...")
if user_input:
    question = user_input

if question:
    st.markdown(f'<div class="chat-bubble-user">🧑 {question}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": question})

    with st.spinner("Agent thinking..."):
        context = prompt.format(
            total_skus     = len(df),
            critical_count = len(critical_skus),
            warning_count  = len(warning_skus),
            healthy_count  = len(healthy_skus),
            critical_data  = critical_skus[["SKU","Product Name","Days of Stock Left","Supplier"]].to_string(index=False),
            warning_data   = warning_skus[["SKU","Product Name","Days of Stock Left"]].to_string(index=False),
            question       = question,
        )
        answer = llm.invoke(context)

    st.markdown(f'<div class="chat-bubble-agent">🤖 {answer}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": answer})

if st.session_state.messages:
    if st.button("🗑 Clear chat"):
        st.session_state.messages = []
        st.rerun()
