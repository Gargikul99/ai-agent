# Supply Chain Intelligence Agent

I built this for supply chain managers who need to monitor 
warehouse inventory, transport performance, shipments, sales, 
and demand forecasts — all in one place.

Managing a supply chain means constantly switching between 
different systems and files to get a complete picture of 
what's happening. This project brings all of that into a 
single interface.

## What it does

When you open the app you get a dashboard showing the health 
of your supply chain across 5 warehouse zones in the US — 
Los Angeles, Chicago, Dallas, New York, and Atlanta.

If something looks off or you want to dig deeper, there's a 
chatbot where you can ask questions in plain English like:

- "Which SKUs are critical in Dallas right now?"
- "Which carrier is underperforming this week?"
- "Are there any delayed shipments out of Chicago?"
- "Will we run out of beverages in LA this month?"

The system figures out which data to look at and gives you 
a direct answer — no need to filter spreadsheets or run reports.

## What's under the hood

The data lives in a DuckDB database with 7 tables covering 
inventory, transport lanes, active shipments, sales history, 
and 30-day demand forecasts. A multi-agent system routes each 
question to the right specialist — a warehouse agent, transport 
agent, shipment agent, sales agent, or forecast agent — depending 
on what's being asked. Gemma 4 (running locally on your machine) 
turns the data into a readable answer.

Everything runs locally — no cloud, no subscription, no data 
leaving your machine.

## Tech stack
Python · DuckDB · Gemma 4 · Ollama · LangChain · Streamlit · Power BI

## How to run

pip install duckdb pandas openpyxl langchain langchain-ollama streamlit

cd pipeline
python schema.py
python seed_data.py
streamlit run dashboard/manager_app.py

## Project status
Currently building — Phase 1 (database and seed data) is complete.