import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))

from agents.orchestrator import run_ai_orchestrator

# Page config
st.set_page_config(
    page_title="Supply Chain Intelligence",
    page_icon="🏭",
    layout="wide"
)

# Header
st.title("🏭 Supply Chain Intelligence Dashboard")
st.markdown("Ask anything about inventory, transport, shipments, sales or forecasts.")
st.divider()

# Zone reference
with st.expander("📍 Zone Reference"):
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Zone A", "Los Angeles")
    col2.metric("Zone B", "Chicago")
    col3.metric("Zone C", "Dallas")
    col4.metric("Zone D", "New York")
    col5.metric("Zone E", "Atlanta")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agents_log" not in st.session_state:
    st.session_state.agents_log = []

# Display chat history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and i // 2 < len(st.session_state.agents_log):
            agents = st.session_state.agents_log[i // 2]
            if agents:
                st.caption(f"🤖 Agents used: {', '.join(agents)}")

# Quick question buttons
st.markdown("**Quick questions:**")
col1, col2, col3, col4 = st.columns(4)

quick_questions = {
    col1: "Which SKUs are critical in Chicago?",
    col2: "Which carrier is performing worst?",
    col3: "Will we run out of stock next week in Dallas?",
    col4: "Give me an overall supply chain health summary"
}

for col, question in quick_questions.items():
    if col.button(question, use_container_width=True):
        st.session_state.pending_question = question

# Chat input
prompt = st.chat_input("Ask about your supply chain...")

# Handle quick question button clicks
if "pending_question" in st.session_state:
    prompt = st.session_state.pending_question
    del st.session_state.pending_question

# Process question
if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get answer
    with st.chat_message("assistant"):
        with st.spinner("Analyzing supply chain data..."):
            try:
                answer, agents_used = run_ai_orchestrator(prompt)
                st.markdown(answer)
                if agents_used:
                    agent_names = {
                        "get_warehouse_status":  "📦 Warehouse",
                        "get_transport_status":  "🚛 Transport",
                        "get_shipment_status":   "📬 Shipments",
                        "get_sales_status":      "💰 Sales",
                        "get_forecast_status":   "🔮 Forecast"
                    }
                    friendly = [agent_names.get(a, a) for a in agents_used]
                    st.caption(f"🤖 Agents used: {', '.join(friendly)}")
                    st.session_state.agents_log.append(agents_used)
                else:
                    st.session_state.agents_log.append([])

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.error(answer)
                st.session_state.agents_log.append([])

        st.session_state.messages.append({"role": "assistant", "content": answer})

# Sidebar
with st.sidebar:
    st.header("📊 Session Stats")
    st.metric("Questions asked", len(st.session_state.messages) // 2)

    if st.session_state.agents_log:
        all_agents = [a for log in st.session_state.agents_log for a in log]
        if all_agents:
            st.markdown("**Most used agents:**")
            from collections import Counter
            agent_names = {
                "get_warehouse_status":  "📦 Warehouse",
                "get_transport_status":  "🚛 Transport",
                "get_shipment_status":   "📬 Shipments",
                "get_sales_status":      "💰 Sales",
                "get_forecast_status":   "🔮 Forecast"
            }
            for agent, count in Counter(all_agents).most_common():
                st.write(f"{agent_names.get(agent, agent)}: {count}x")

    st.divider()
    if st.button("🗑️ Clear chat history"):
        st.session_state.messages = []
        st.session_state.agents_log = []
        st.rerun()