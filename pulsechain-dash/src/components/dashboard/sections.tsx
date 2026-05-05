import { lazy, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import { KpiGrid, SectionCard, StatusPill } from "./primitives";
import type { HealthStatus, KpiTile, ForecastSnapshot, ForecastItem, ForecastByZone } from "@/lib/types";

const ShipmentsMap = lazy(() => import("./shipments-map"));

const tooltipStyle = {
  backgroundColor: "var(--popover)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  color: "var(--foreground)",
  fontSize: 12,
};

export function InventorySection({ flash }: { flash: boolean }) {
  const { data } = useQuery({ queryKey: ["inventory"], queryFn: api.inventory });
  if (!data) return <SectionCard title="Inventory & Stock"><Skeleton /></SectionCard>;
  return (
    <SectionCard title="Inventory & Stock" subtitle={`Updated ${fmt(data.updatedAt)}`} flash={flash}>
      <KpiGrid tiles={data.kpis} />
      <div className="mt-5 grid lg:grid-cols-2 gap-5">
        <div>
          <h3 className="text-sm font-medium mb-2 text-muted-foreground">Stock by Warehouse</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={data.byWarehouse}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="warehouse" stroke="var(--muted-foreground)" fontSize={11} />
              <YAxis stroke="var(--muted-foreground)" fontSize={11} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--accent)", opacity: 0.3 }} />
              <Bar dataKey="units" fill="var(--primary)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div>
          <h3 className="text-sm font-medium mb-2 text-muted-foreground">Low Stock Alerts</h3>
          <div className="space-y-2 max-h-[180px] overflow-auto pr-1">
            {data.lowStock.map((item) => (
              <div key={item.sku} className="flex items-center justify-between gap-3 rounded-md bg-background/40 px-3 py-2 text-sm">
                <div className="min-w-0">
                  <div className="font-medium truncate">{item.name}</div>
                  <div className="text-xs text-muted-foreground">{item.sku} · {item.warehouse}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-muted-foreground">{item.onHand} / {item.reorderPoint}</div>
                  <StatusPill status={item.status} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

export function ShipmentsSection({ flash }: { flash: boolean }) {
  const { data } = useQuery({ queryKey: ["shipments"], queryFn: api.shipments });
  if (!data) return <SectionCard title="Shipments & Logistics"><Skeleton /></SectionCard>;
  return (
    <SectionCard title="Shipments & Logistics" subtitle={`Updated ${fmt(data.updatedAt)}`} flash={flash}>
      <KpiGrid tiles={data.kpis} />
      <div className="mt-5">
        <h3 className="text-sm font-medium mb-2 text-muted-foreground">Live Shipment Tracking</h3>
        <Suspense fallback={<div className="h-[320px] rounded-md bg-background/40 animate-pulse" />}>
          <ShipmentsMap shipments={data.inTransit} />
        </Suspense>
      </div>
      <div className="mt-5 overflow-auto">
        <table className="w-full text-sm">
          <thead className="text-xs uppercase tracking-wider text-muted-foreground">
            <tr className="text-left">
              <th className="py-2 pr-3">Shipment</th>
              <th className="py-2 pr-3">Route</th>
              <th className="py-2 pr-3">Carrier</th>
              <th className="py-2 pr-3">ETA</th>
              <th className="py-2 pr-3">Delay</th>
              <th className="py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.inTransit.map((s) => (
              <tr key={s.id} className="border-t border-border/40">
                <td className="py-2 pr-3 font-mono text-xs">{s.id}</td>
                <td className="py-2 pr-3">{s.origin} → {s.destination}</td>
                <td className="py-2 pr-3 text-muted-foreground">{s.carrier}</td>
                <td className="py-2 pr-3">{s.eta}</td>
                <td className="py-2 pr-3">{s.delayHours > 0 ? `+${s.delayHours}h` : "—"}</td>
                <td className="py-2"><StatusPill status={s.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}

export function OrdersSection({ flash }: { flash: boolean }) {
  const { data } = useQuery({ queryKey: ["orders"], queryFn: api.orders });
  if (!data) return <SectionCard title="Orders & Fulfillment"><Skeleton /></SectionCard>;
  return (
    <SectionCard title="Orders & Fulfillment" subtitle={`Updated ${fmt(data.updatedAt)}`} flash={flash}>
      <KpiGrid tiles={data.kpis} />
      <div className="mt-5 grid lg:grid-cols-2 gap-5">
        <div>
          <h3 className="text-sm font-medium mb-2 text-muted-foreground">Fulfillment Trend</h3>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={data.fulfillmentTrend}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="hour" stroke="var(--muted-foreground)" fontSize={11} />
              <YAxis stroke="var(--muted-foreground)" fontSize={11} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line type="monotone" dataKey="orders" stroke="var(--primary)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="fulfilled" stroke="var(--status-healthy)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div>
          <h3 className="text-sm font-medium mb-2 text-muted-foreground">Recent Orders</h3>
          <div className="space-y-2 max-h-[180px] overflow-auto pr-1">
            {data.recent.map((o) => (
              <div key={o.id} className="flex items-center justify-between gap-3 rounded-md bg-background/40 px-3 py-2 text-sm">
                <div className="min-w-0">
                  <div className="font-medium truncate">{o.customer}</div>
                  <div className="text-xs text-muted-foreground">{o.id} · {o.items} items · {o.placedAt}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">${o.value.toLocaleString()}</div>
                  <StatusPill status={o.status} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

export function SuppliersSection({ flash }: { flash: boolean }) {
  const { data } = useQuery({ queryKey: ["suppliers"], queryFn: api.suppliers });
  if (!data) return <SectionCard title="Suppliers & Procurement"><Skeleton /></SectionCard>;
  return (
    <SectionCard title="Suppliers & Procurement" subtitle={`Updated ${fmt(data.updatedAt)}`} flash={flash}>
      <KpiGrid tiles={data.kpis} />
      <div className="mt-5 overflow-auto">
        <table className="w-full text-sm">
          <thead className="text-xs uppercase tracking-wider text-muted-foreground">
            <tr className="text-left">
              <th className="py-2 pr-3">Supplier</th>
              <th className="py-2 pr-3">Region</th>
              <th className="py-2 pr-3">On-Time</th>
              <th className="py-2 pr-3">Lead Time</th>
              <th className="py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.suppliers.map((s) => (
              <tr key={s.id} className="border-t border-border/40">
                <td className="py-2 pr-3 font-medium">{s.name}</td>
                <td className="py-2 pr-3 text-muted-foreground">{s.region}</td>
                <td className="py-2 pr-3">{Math.round(s.onTimeRate * 100)}%</td>
                <td className="py-2 pr-3">{s.leadTimeDays}d</td>
                <td className="py-2"><StatusPill status={s.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}

export function ForecastSection({ flash }: { flash: boolean }) {
  const { data } = useQuery({ queryKey: ["forecasts"], queryFn: api.forecasts });
  if (!data) return <SectionCard title="Forecast & Demand Intelligence"><Skeleton /></SectionCard>;

  const maxRisk = Math.max(...data.byZone.map((z) => z.skus_at_risk));
  const maxDemand = Math.max(...data.byZone.map((z) => z.total_demand));

  return (
    <SectionCard title="Forecast & Demand Intelligence" subtitle={`Updated ${fmt(data.updatedAt)}`} flash={flash}>
      <KpiGrid tiles={data.kpis} />

      <div className="mt-5 grid lg:grid-cols-2 gap-5">
        <div>
          <h3 className="text-sm font-medium mb-2 text-muted-foreground">Stockout risk by zone</h3>
          <div className="space-y-2">
            {[...data.byZone].sort((a, b) => b.skus_at_risk - a.skus_at_risk).map((zone) => {
              const pct = Math.round((zone.skus_at_risk / maxRisk) * 100);
              const color = zone.skus_at_risk > 19 ? "var(--status-critical)"
                          : zone.skus_at_risk > 17 ? "var(--status-warning)"
                          : "var(--status-healthy)";
              return (
                <div key={zone.city} className="flex items-center gap-3">
                  <div className="text-xs w-24 shrink-0">{zone.city}</div>
                  <div className="flex-1 h-2 rounded-full bg-background/40">
                    <div style={{ width: `${pct}%`, background: color }} className="h-2 rounded-full" />
                  </div>
                  <div className="text-xs text-muted-foreground w-6 text-right">{zone.skus_at_risk}</div>
                </div>
              );
            })}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium mb-2 text-muted-foreground">2-week demand by zone</h3>
          <div className="space-y-2">
            {[...data.byZone].sort((a, b) => b.total_demand - a.total_demand).map((zone) => {
              const pct = Math.round((zone.total_demand / maxDemand) * 100);
              return (
                <div key={zone.city} className="flex items-center gap-3">
                  <div className="text-xs w-24 shrink-0">{zone.city}</div>
                  <div className="flex-1 h-2 rounded-full bg-background/40">
                    <div style={{ width: `${pct}%` }} className="h-2 rounded-full bg-primary" />
                  </div>
                  <div className="text-xs text-muted-foreground w-12 text-right">{zone.total_demand.toLocaleString()}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="mt-5">
  <h3 className="text-sm font-medium mb-2 text-muted-foreground">
    Forecast confidence by zone
  </h3>
  <div className="space-y-3">
    {data.byZone.map((zone) => (
      <div key={zone.city} className="flex items-center justify-between rounded-md bg-background/40 px-3 py-2 text-sm">
        <div className="font-medium">{zone.city}</div>
        <div className="text-xs text-muted-foreground">
          {zone.skus_at_risk} SKUs at risk · {zone.total_demand.toLocaleString()} units demand
        </div>
        <div className="text-xs text-muted-foreground">
          ±{zone.avg_uncertainty.toFixed(1)} uncertainty
        </div>
      </div>
    ))}
  </div>
</div>
        
    </SectionCard>
  );
}

function Skeleton() {
  return <div className="h-40 animate-pulse rounded-md bg-background/40" />;
}
function fmt(iso: string) {
  return new Date(iso).toLocaleTimeString();
}
