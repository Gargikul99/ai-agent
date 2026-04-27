"""
Level 1 Stock Analysis Agent — FMCG Warehouse
Ask questions in plain English about your inventory.
Powered by Gemma 4 via Ollama (local, free, offline).
"""

import pandas as pd
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

FILE = "fmcg_warehouse_inventory.xlsx"

# Load all three sheets
df_inventory = pd.read_excel(FILE, sheet_name="Inventory Data")
df_status    = pd.read_excel(FILE, sheet_name="Stock Status Summary", header=None)
df_category  = pd.read_excel(FILE, sheet_name="Category Summary")

# Pre-compute key stats for fast context building
total_skus    = len(df_inventory)
critical_skus = df_inventory[df_inventory["Current Stock (Units)"] < df_inventory["Reorder Point (Units)"] * 0.5]
warning_skus  = df_inventory[(df_inventory["Current Stock (Units)"] >= df_inventory["Reorder Point (Units)"] * 0.5) &
                              (df_inventory["Current Stock (Units)"] <  df_inventory["Reorder Point (Units)"])]
healthy_skus  = df_inventory[df_inventory["Current Stock (Units)"] >= df_inventory["Reorder Point (Units)"]]

# Start Gemma 4 via Ollama
llm = OllamaLLM(model="gemma4:e2b")

# Prompt template
prompt = PromptTemplate.from_template("""
You are an expert supply chain and warehouse analyst. You are analyzing a retail FMCG warehouse inventory dataset.

DATASET OVERVIEW:
- Total SKUs: {total_skus}
- Critical stock SKUs (below 50% of reorder point): {critical_count}
- Warning SKUs (below reorder point): {warning_count}
- Healthy SKUs: {healthy_count}

CRITICAL SKUs (need immediate action):
{critical_data}

WARNING SKUs (need attention soon):
{warning_data}

CATEGORY SUMMARY:
{category_data}

FULL INVENTORY SAMPLE (first 15 rows):
{inventory_sample}

Answer the following question clearly, concisely, and like a professional supply chain analyst.
Use specific SKU names, numbers, and actionable recommendations where relevant.

Question: {question}
""")

print("\n📦  FMCG Warehouse Stock Agent — Level 1")
print("=" * 45)
print(f"✅  Loaded {total_skus} SKUs across {df_inventory['Category'].nunique()} categories")
print(f"🔴  Critical: {len(critical_skus)} SKUs   🟡 Warning: {len(warning_skus)} SKUs   🟢 Healthy: {len(healthy_skus)} SKUs")
print("=" * 45)
print("Type your question or 'exit' to quit.\n")

# Suggested starter questions
starters = [
    "Which SKUs need immediate restocking?",
    "What is the overall stock health of the warehouse?",
    "Which category has the most critical items?",
    "Which items will run out within 3 days?",
    "Who are my most critical suppliers right now?",
]
print("💡 Try asking:")
for q in starters:
    print(f"   → {q}")
print()

while True:
    question = input("Your question: ").strip()
    if not question:
        continue
    if question.lower() == "exit":
        print("Goodbye!")
        break

    # Build context
    context = prompt.format(
        total_skus      = total_skus,
        critical_count  = len(critical_skus),
        warning_count   = len(warning_skus),
        healthy_count   = len(healthy_skus),
        critical_data   = critical_skus[["SKU","Product Name","Category","Current Stock (Units)",
                                          "Reorder Point (Units)","Days of Stock Left","Supplier"]].to_string(index=False),
        warning_data    = warning_skus[["SKU","Product Name","Category","Current Stock (Units)",
                                         "Reorder Point (Units)","Days of Stock Left","Supplier"]].to_string(index=False),
        category_data   = df_category.to_string(index=False),
        inventory_sample= df_inventory.head(15).to_string(index=False),
        question        = question,
    )

    print("\n🤖 Agent thinking...\n")
    answer = llm.invoke(context)
    print(f"Agent: {answer}\n")
    print("-" * 45 + "\n")
