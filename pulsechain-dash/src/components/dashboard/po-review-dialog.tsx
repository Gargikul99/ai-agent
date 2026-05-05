import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api } from "@/lib/api";
import type { DraftPO } from "@/lib/types";
import { StatusPill } from "./primitives";
import { CheckCircle2, XCircle, Clock, Sparkles } from "lucide-react";

export function PoReviewDialog({ draft, open, onClose }: { draft: DraftPO | null; open: boolean; onClose: () => void }) {
  const qc = useQueryClient();
  const [qty, setQty] = useState(draft?.suggestedQty ?? 0);
  const [supplierId, setSupplierId] = useState(draft?.suggestedSupplier.supplierId ?? "");

  // Reset state when draft changes
  if (draft && supplierId === "" ) {
    setQty(draft.suggestedQty);
    setSupplierId(draft.suggestedSupplier.supplierId);
  }

  const allSuppliers = draft ? [draft.suggestedSupplier, ...draft.alternativeSuppliers] : [];
  const selected = allSuppliers.find((s) => s.supplierId === supplierId) ?? draft?.suggestedSupplier;
  const total = selected ? Math.round(qty * selected.unitPrice * 100) / 100 : 0;

  const place = useMutation({
    mutationFn: () => api.placePO(draft!.id, { qty, supplierId }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["po_drafts"] });
      onClose();
    },
  });
  const reject = useMutation({
    mutationFn: () => api.rejectPO(draft!.id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["po_drafts"] }); onClose(); },
  });
  const snooze = useMutation({
    mutationFn: () => api.snoozePO(draft!.id, 24),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["po_drafts"] }); onClose(); },
  });

  if (!draft) return null;

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl bg-card text-card-foreground border-border/40">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Review Draft {draft.id}
            <StatusPill status={draft.urgency} />
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="rounded-md bg-background/40 p-3 text-sm">
            <div className="font-medium">{draft.productName} <span className="font-mono text-xs text-muted-foreground">({draft.sku})</span></div>
            <div className="text-xs text-muted-foreground mt-1">
              {draft.warehouse} · On hand <span className="text-[color:var(--status-critical)] font-medium">{draft.onHand}</span> / reorder {draft.reorderPoint} · Avg demand {draft.avgDailyDemand}/day
            </div>
          </div>

          <div className="rounded-md bg-background/40 p-3 text-sm flex gap-2">
            <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
            <div>
              <div className="text-xs uppercase tracking-wider text-muted-foreground mb-1">AI Rationale</div>
              <div>{draft.rationale}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs">Quantity</Label>
              <Input
                type="number"
                value={qty}
                onChange={(e) => setQty(Number(e.target.value))}
                className="bg-background/40 border-border/40 mt-1"
              />
            </div>
            <div>
              <Label className="text-xs">Supplier</Label>
              <Select value={supplierId} onValueChange={setSupplierId}>
                <SelectTrigger className="bg-background/40 border-border/40 mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {allSuppliers.map((s) => (
                    <SelectItem key={s.supplierId} value={s.supplierId}>
                      {s.supplierName} — ${s.unitPrice}/u · {s.leadTimeDays}d · {Math.round(s.onTimeRate * 100)}% OT
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex justify-between items-center rounded-md bg-background/40 p-3 text-sm">
            <div className="text-muted-foreground text-xs">Estimated total</div>
            <div className="text-2xl font-semibold text-[color:var(--status-healthy)]">${total.toLocaleString()}</div>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-2">
          <Button variant="ghost" onClick={() => reject.mutate()} disabled={reject.isPending}>
            <XCircle className="h-4 w-4" /> Reject
          </Button>
          <Button variant="outline" onClick={() => snooze.mutate()} disabled={snooze.isPending}>
            <Clock className="h-4 w-4" /> Snooze 24h
          </Button>
          <Button onClick={() => place.mutate()} disabled={place.isPending}>
            <CheckCircle2 className="h-4 w-4" /> {place.isPending ? "Placing…" : "Place PO"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
