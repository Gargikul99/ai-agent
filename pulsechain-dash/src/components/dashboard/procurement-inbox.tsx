import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { KpiGrid, SectionCard, StatusPill } from "./primitives";
import { Button } from "@/components/ui/button";
import { PoReviewDialog } from "./po-review-dialog";
import { Bot, ChevronRight } from "lucide-react";
import type { DraftPO } from "@/lib/types";

export function ProcurementSection({ flash }: { flash: boolean }) {
  const { data } = useQuery({ queryKey: ["po_drafts"], queryFn: api.poDrafts });
  const [active, setActive] = useState<DraftPO | null>(null);

  if (!data) return <SectionCard title="Procurement Inbox"><div className="h-32 animate-pulse rounded-md bg-background/40" /></SectionCard>;

  return (
    <SectionCard
      title="Procurement Inbox"
      subtitle={`AI-drafted POs awaiting your approval · Updated ${new Date(data.updatedAt).toLocaleTimeString()}`}
      flash={flash}
    >
      <KpiGrid tiles={data.kpis} />

      <div className="mt-5">
        <h3 className="text-sm font-medium mb-2 text-muted-foreground flex items-center gap-2">
          <Bot className="h-4 w-4 text-primary" /> Pending Approval ({data.drafts.length})
        </h3>
        {data.drafts.length === 0 ? (
          <div className="rounded-md bg-background/40 p-6 text-center text-sm text-muted-foreground">
            No drafts pending. The AI will queue new POs here when inventory triggers.
          </div>
        ) : (
          <div className="space-y-2">
            {data.drafts.map((d) => (
              <button
                key={d.id}
                onClick={() => setActive(d)}
                className="w-full flex items-center justify-between gap-3 rounded-md bg-background/40 hover:bg-background/60 transition-colors px-3 py-3 text-sm text-left"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-muted-foreground">{d.id}</span>
                    <StatusPill status={d.urgency} />
                  </div>
                  <div className="mt-1 font-medium truncate">{d.productName}</div>
                  <div className="text-xs text-muted-foreground truncate">
                    {d.warehouse} · {d.suggestedQty} units from {d.suggestedSupplier.supplierName} · ETA {d.estimatedEta}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-base font-semibold">${d.totalCost.toLocaleString()}</div>
                  <div className="text-xs text-muted-foreground">on hand {d.onHand}/{d.reorderPoint}</div>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6">
        <h3 className="text-sm font-medium mb-2 text-muted-foreground">Recently Placed POs</h3>
        <div className="overflow-auto">
          <table className="w-full text-sm">
            <thead className="text-xs uppercase tracking-wider text-muted-foreground">
              <tr className="text-left">
                <th className="py-2 pr-3">PO</th>
                <th className="py-2 pr-3">Item</th>
                <th className="py-2 pr-3">Supplier</th>
                <th className="py-2 pr-3">Qty</th>
                <th className="py-2 pr-3">Total</th>
                <th className="py-2 pr-3">By</th>
                <th className="py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.placed.map((p) => (
                <tr key={p.id} className="border-t border-border/40">
                  <td className="py-2 pr-3 font-mono text-xs">{p.id}</td>
                  <td className="py-2 pr-3">{p.productName}</td>
                  <td className="py-2 pr-3 text-muted-foreground">{p.supplierName}</td>
                  <td className="py-2 pr-3">{p.qty}</td>
                  <td className="py-2 pr-3">${p.totalCost.toLocaleString()}</td>
                  <td className="py-2 pr-3 text-muted-foreground">{p.placedBy}</td>
                  <td className="py-2">
                    <span className="text-xs rounded-full px-2 py-0.5 bg-background/60 ring-1 ring-border/40 capitalize">
                      {p.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <PoReviewDialog draft={active} open={!!active} onClose={() => setActive(null)} />
    </SectionCard>
  );
}
