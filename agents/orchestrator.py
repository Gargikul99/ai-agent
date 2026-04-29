import json
import os
import sys
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Tool definitions for Groq
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_warehouse_status",
            "description": "Get inventory stock levels, critical SKUs, reorder alerts and ATP. Use for questions about stock, inventory, critical items, reorder needs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone": {
                        "type": "string",
                        "description": "Zone: A=Los Angeles, B=Chicago, C=Dallas, D=New York, E=Atlanta, ALL=all zones"
                    }
                },
                "required": ["zone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_transport_status",
            "description": "Get carrier performance, lane delays, route optimization. Use for questions about carriers, routes, freight, delivery performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone": {
                        "type": "string",
                        "description": "Zone: A=Los Angeles, B=Chicago, C=Dallas, D=New York, E=Atlanta, ALL=all zones"
                    }
                },
                "required": ["zone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_shipment_status",
            "description": "Get active shipments, delayed orders, lost shipments, value at risk. Use for questions about shipments, deliveries, orders in transit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone": {
                        "type": "string",
                        "description": "Zone: A=Los Angeles, B=Chicago, C=Dallas, D=New York, E=Atlanta, ALL=all zones"
                    }
                },
                "required": ["zone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_sales_status",
            "description": "Get sales velocity, top SKUs, revenue trends, week over week changes. Use for questions about sales, revenue, best sellers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone": {
                        "type": "string",
                        "description": "Zone: A=Los Angeles, B=Chicago, C=Dallas, D=New York, E=Atlanta, ALL=all zones"
                    }
                },
                "required": ["zone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_forecast_status",
            "description": "Get 2-week demand forecasts, stockout predictions, demand outlook. Use for questions about future demand, will we run out, next week.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone": {
                        "type": "string",
                        "description": "Zone: A=Los Angeles, B=Chicago, C=Dallas, D=New York, E=Atlanta, ALL=all zones"
                    }
                },
                "required": ["zone"]
            }
        }
    }
]

def execute_tool(tool_name, zone):
    zone_ids = None if zone == "ALL" else [zone]

    if tool_name == "get_warehouse_status":
        from agents.warehouse_agent import get_warehouse_stats, get_atp
        stats, critical, warning, healthy, df = get_warehouse_stats(zone_ids)
        atp_df  = get_atp(zone_ids)
        at_risk = atp_df[atp_df["stockout_prediction"] != "Beyond 3 weeks"]
        return {
            "total_skus":         stats["total_skus"],
            "critical":           stats["critical_count"],
            "warning":            stats["warning_count"],
            "healthy":            stats["healthy_count"],
            "most_urgent_sku":    stats["most_urgent_sku"],
            "most_urgent_days":   stats["most_urgent_days"],
            "most_urgent_zone":   stats["most_urgent_zone"],
            "stockout_this_week": stats["stockout_this_week"],
            "stockout_week2":     stats["stockout_week2"],
            "total_reorder_qty":  stats["total_reorder_qty"],
            "critical_skus": critical[["sku_id","zone_id","product_name",
                                        "current_stock","days_of_stock",
                                        "action_required","supplier"
                                        ]].head(5).to_dict("records"),
            "atp_at_risk": at_risk[["sku_id","zone_id","product_name",
                                     "atp_week1","atp_week2",
                                     "stockout_prediction"]].head(5).to_dict("records")
        }

    elif tool_name == "get_transport_status":
        from agents.transport_agent import get_transport_stats
        stats, df, delayed, expensive, poor, carrier_summary, best = \
            get_transport_stats(zone_ids)
        return {
            "total_lanes":         stats["total_lanes"],
            "on_time_pct":         stats["on_time_pct"],
            "delayed_lanes":       stats["delayed_lanes"],
            "best_carrier":        stats["best_carrier"],
            "best_carrier_score":  stats["best_carrier_score"],
            "worst_carrier":       stats["worst_carrier"],
            "worst_carrier_score": stats["worst_carrier_score"],
            "avg_cost_per_kg":     stats["avg_cost_per_kg"],
            "carrier_summary": carrier_summary[["carrier","on_time_pct",
                                                 "avg_perf_score"]].to_dict("records")
        }

    elif tool_name == "get_shipment_status":
        from agents.shipment_agent import get_shipment_stats
        stats, df, delayed, held, lost, in_transit, pod = \
            get_shipment_stats(zone_ids)
        return {
            "total_shipments":        stats["total_shipments"],
            "in_transit":             stats["in_transit"],
            "delayed":                stats["delayed"],
            "held_at_hub":            stats["held_at_hub"],
            "lost_in_transit":        stats["lost_in_transit"],
            "value_at_risk":          stats["value_at_risk"],
            "most_affected_customer": stats["most_affected_customer"],
            "most_delayed_carrier":   stats["most_delayed_carrier"],
            "on_time_pct":            stats["on_time_delivery_pct"],
            "delayed_shipments": delayed[["shipment_id","customer",
                                           "carrier","delay_days",
                                           "value_usd"]].head(5).to_dict("records")
        }

    elif tool_name == "get_sales_status":
        from agents.sales_agent import get_sales_stats
        stats, velocity, trend, channel, category = \
            get_sales_stats(zone_ids)
        return {
            "total_units_30d":   stats["total_units_30d"],
            "total_revenue_30d": stats["total_revenue_30d"],
            "top_sku":           stats["top_sku"],
            "top_category":      stats["top_category"],
            "wow_change_pct":    stats["wow_change_pct"],
            "slow_moving_count": stats["slow_moving_count"],
            "trend": trend.to_dict("records"),
            "category_performance": category[["category","total_units",
                                               "revenue"]].to_dict("records")
        }

    elif tool_name == "get_forecast_status":
        from agents.forecast_agent import get_forecast_stats
        stats, df, at_risk = get_forecast_stats(zone_ids)
        return {
            "skus_at_risk_2weeks": stats["skus_at_risk_2weeks"],
            "total_2week_demand":  stats["total_2week_demand"],
            "worst_case_demand":   stats["total_2week_worst_case"],
            "most_at_risk_sku":    stats["most_at_risk_sku"],
            "most_at_risk_zone":   stats["most_at_risk_zone"],
            "largest_stock_gap":   stats["largest_stock_gap"],
            "stockout_risks": at_risk[["sku_id","zone_id","product_name",
                                        "current_stock","forecast_2weeks",
                                        "stock_gap"]].head(5).to_dict("records")
        }

def run_ai_orchestrator(question):
    print(f"Question: {question}")
    print("Groq deciding which agents to call...\n")

    messages = [
        {
            "role": "system",
            "content": """You are a supply chain intelligence assistant.
Use tools to answer questions about warehouse inventory, transport, shipments, sales and forecasts.
Give SHORT bullet point answers. Maximum 5 bullets. Always include specific numbers."""
        },
        {
            "role": "user",
            "content": question
        }
    ]

    # First call — Groq decides which tools to call
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        max_tokens=1000
    )

    response_message = response.choices[0].message
    agents_used = []

    # Process tool calls if any
    if response_message.tool_calls:
        messages.append(response_message)

        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            args      = json.loads(tool_call.function.arguments)
            zone      = args.get("zone", "ALL")

            print(f"Calling agent: {tool_name} (zone={zone})")
            agents_used.append(tool_name)

            result = execute_tool(tool_name, zone)

            messages.append({
                "role":         "tool",
                "tool_call_id": tool_call.id,
                "content":      json.dumps(result)
            })

        # Second call — Groq generates final answer using tool results
        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1000
        )
        answer = final_response.choices[0].message.content

    else:
        answer = response_message.content

    print(f"Agents used: {agents_used}")
    print(f"\nAnswer:\n{answer}")
    return answer, agents_used

if __name__ == "__main__":
    questions = [
        "Which SKUs are critical in Chicago?",
        "Which carrier is performing worst?",
        "Will we run out of stock next week in Dallas?",
        "Give me an overall supply chain health summary",
    ]

    for q in questions:
        print("\n" + "="*60)
        run_ai_orchestrator(q)
        print()