import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { KpiGrid, SectionCard } from "./primitives";

export function ForecastSection() {
  const { data, isLoading } = useQuery({
    queryKey: ["forecasts"],
    queryFn: api.forecasts,
    refetchInterval: 30000,
  });

  if (isLoading || !data) return null;

  const maxRisk = Math.max(...data.byZone.map((z) => z.skus_at_risk));
  const maxDemand = Math.max(...data.byZone.map((z) => z.total_demand));

  return (
    <div style={{ marginBottom: "2rem" }}>
      <SectionCard
        title="Forecast & Demand Intelligence"
        subtitle={`Updated ${new Date(data.updatedAt).toLocaleTimeString()}`}
      >
        <KpiGrid tiles={data.kpis} />
      </SectionCard>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginTop: "12px", marginBottom: "12px" }}>
        <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "14px 16px" }}>
          <p style={{ fontSize: "11px", color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.7px", marginBottom: "12px" }}>
            Stockout risk by zone
          </p>
          {[...data.byZone].sort((a, b) => b.skus_at_risk - a.skus_at_risk).map((zone) => {
            const pct = Math.round((zone.skus_at_risk / maxRisk) * 100);
            const color = zone.skus_at_risk > 19 ? "#E24B4A" : zone.skus_at_risk > 17 ? "#EF9F27" : "#639922";
            return (
              <div key={zone.city} style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                <div style={{ fontSize: "12px", color: "var(--color-text-primary)", width: "90px", flexShrink: 0 }}>{zone.city}</div>
                <div style={{ flex: 1, background: "var(--color-background-secondary)", borderRadius: "3px", height: "8px" }}>
                  <div style={{ width: `${pct}%`, height: "8px", borderRadius: "3px", background: color }} />
                </div>
                <div style={{ fontSize: "12px", color: "var(--color-text-secondary)", width: "28px", textAlign: "right", flexShrink: 0 }}>{zone.skus_at_risk}</div>
              </div>
            );
          })}
        </div>

        <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "14px 16px" }}>
          <p style={{ fontSize: "11px", color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.7px", marginBottom: "12px" }}>
            2-week demand forecast by zone
          </p>
          {[...data.byZone].sort((a, b) => b.total_demand - a.total_demand).map((zone) => {
            const pct = Math.round((zone.total_demand / maxDemand) * 100);
            return (
              <div key={zone.city} style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                <div style={{ fontSize: "12px", color: "var(--color-text-primary)", width: "90px", flexShrink: 0 }}>{zone.city}</div>
                <div style={{ flex: 1, background: "var(--color-background-secondary)", borderRadius: "3px", height: "8px" }}>
                  <div style={{ width: `${pct}%`, height: "8px", borderRadius: "3px", background: "#378ADD" }} />
                </div>
                <div style={{ fontSize: "12px", color: "var(--color-text-secondary)", width: "36px", textAlign: "right", flexShrink: 0 }}>{zone.total_demand.toLocaleString()}</div>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-lg)", padding: "14px 16px" }}>
        <p style={{ fontSize: "11px", color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.7px", marginBottom: "12px" }}>
          Top SKUs at stockout risk (2 weeks)
        </p>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
          <thead>
            <tr>
              {["SKU", "Product", "Zone", "Stock", "2-wk demand", "Gap", "Status"].map(h => (
                <th key={h} style={{ textAlign: "left", color: "var(--color-text-secondary)", fontWeight: 500, padding: "4px 8px", borderBottom: "0.5px solid var(--color-border-tertiary)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.atRisk.map((item) => {
              const badgeColor = item.status === "critical"
                ? { bg: "#FCEBEB", color: "#A32D2D" }
                : { bg: "#FAEEDA", color: "#854F0B" };
              return (
                <tr key={`${item.sku_id}-${item.zone_id}`}>
                  <td style={{ padding: "6px 8px", borderBottom: "0.5px solid var(--color-border-tertiary)", color: "var(--color-text-secondary)" }}>{item.sku_id}</td>
                  <td style={{ padding: "6px 8px", borderBottom: "0.5px solid var(--color-border-tertiary)", color: "var(--color-text-primary)" }}>{item.product_name}</td>
                  <td style={{ padding: "6px 8px", borderBottom: "0.5px solid var(--color-border-tertiary)", color: "var(--color-text-secondary)" }}>{item.city}</td>
                  <td style={{ padding: "6px 8px", borderBottom: "0.5px solid var(--color-border-tertiary)", color: "var(--color-text-primary)" }}>{item.current_stock}</td>
                  <td style={{ padding: "6px 8px", borderBottom: "0.5px solid var(--color-border-tertiary)", color: "var(--color-text-primary)" }}>{Math.round(item.forecasted_demand * 14).toLocaleString()}</td>
                  <td style={{ padding: "6px 8px", borderBottom: "0.5px solid var(--color-border-tertiary)", color: "#E24B4A", fontWeight: 500 }}>{item.stock_gap.toLocaleString()}</td>
                  <td style={{ padding: "6px 8px", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
                    <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: "4px", fontSize: "11px", fontWeight: 500, background: badgeColor.bg, color: badgeColor.color }}>
                      {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}