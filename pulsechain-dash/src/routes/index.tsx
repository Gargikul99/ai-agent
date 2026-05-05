import { createFileRoute } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { Activity, Radio } from "lucide-react";
import { useKafkaStream } from "@/hooks/use-kafka-stream";
import {
  InventorySection,
  OrdersSection,
  ShipmentsSection,
  SuppliersSection,
  ForecastSection 
} from "@/components/dashboard/sections";
import { ProcurementSection } from "@/components/dashboard/procurement-inbox";
import { ChatPanel } from "@/components/dashboard/chat-panel";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import type { SectionKey } from "@/lib/api-config";

export const Route = createFileRoute("/")({
  component: Dashboard,
  head: () => ({
    meta: [
      { title: "Supply Chain Command Center" },
      {
        name: "description",
        content:
          "Real-time supply chain monitoring dashboard with Kafka-driven updates and AI assistant.",
      },
    ],
  }),
});

function Dashboard() {
  const qc = useQueryClient();
  const [flash, setFlash] = useState<Record<SectionKey, boolean>>({
    inventory: false, shipments: false, orders: false, suppliers: false, po_drafts: false,
  });

  const { status, lastEventAt } = useKafkaStream((section) => {
    const targets: SectionKey[] =
      section === "all"
        ? ["inventory", "shipments", "orders", "suppliers", "po_drafts"]
        : [section];
    targets.forEach((t) => {
      qc.invalidateQueries({ queryKey: [t] });
      setFlash((f) => ({ ...f, [t]: true }));
    });
  });

  // Clear flash after 1.2s
  useEffect(() => {
    const id = setTimeout(
      () => setFlash({ inventory: false, shipments: false, orders: false, suppliers: false, po_drafts: false }),
      1200,
    );
    return () => clearTimeout(id);
  }, [flash.inventory, flash.shipments, flash.orders, flash.suppliers, flash.po_drafts]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border/40 bg-card/40 backdrop-blur sticky top-0 z-10">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="h-6 w-6 text-primary" />
            <div>
              <h1 className="text-xl font-semibold tracking-tight">
                Supply Chain Command Center
              </h1>
              <p className="text-xs text-muted-foreground">
                Live monitoring · Kafka-driven updates
              </p>
            </div>
          </div>
          <StreamStatusBadge status={status} lastEventAt={lastEventAt} />
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-6 grid lg:grid-cols-[1fr_380px] gap-6">
        <div className="space-y-6 min-w-0">
          <ProcurementSection flash={flash.po_drafts} />
          <InventorySection flash={flash.inventory} />
          <ShipmentsSection flash={flash.shipments} />
          <ForecastSection flash={flash.inventory} />
          <OrdersSection flash={flash.orders} />
          <SuppliersSection flash={flash.suppliers} />
        </div>
        <aside className="lg:sticky lg:top-[88px] lg:h-[calc(100vh-104px)]">
          <ChatPanel />
        </aside>
      </main>
    </div>
  );
}

function StreamStatusBadge({
  status,
  lastEventAt,
}: {
  status: ReturnType<typeof useKafkaStream>["status"];
  lastEventAt: Date | null;
}) {
  const map = {
    live: { label: "Live", color: "var(--status-healthy)" },
    connecting: { label: "Connecting…", color: "var(--status-warning)" },
    offline: { label: "Offline", color: "var(--status-critical)" },
    mock: { label: "Demo (mock stream)", color: "var(--status-info)" },
  } as const;
  const cur = map[status];
  return (
    <div className="flex items-center gap-2 rounded-full bg-background/50 ring-1 ring-border/40 px-3 py-1.5 text-xs">
      <Radio
        className={cn("h-3.5 w-3.5", status === "live" && "animate-pulse")}
        style={{ color: cur.color }}
      />
      <span className="font-medium">{cur.label}</span>
      {lastEventAt && (
        <span className="text-muted-foreground">
          · last event {lastEventAt.toLocaleTimeString()}
        </span>
      )}
    </div>
  );
}
