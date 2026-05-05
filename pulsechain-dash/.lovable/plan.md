
# Auto-Generated Purchase Orders with Human Approval

Yes — this fits naturally on top of the existing inventory + suppliers data. The idea: the system continuously watches inventory, drafts a PO when a SKU breaches its reorder point, picks the best supplier, and parks it in a "Pending Approval" queue. A human just reviews the draft and clicks **Place PO** (or **Edit** / **Reject**).

## User Flow

1. Kafka pushes an inventory update → backend rule engine sees `onHand <= reorderPoint`.
2. Backend drafts a PO: chooses supplier, computes order quantity, estimates cost + ETA.
3. Draft appears in a new **Procurement Inbox** panel on the dashboard with a red/amber badge.
4. Human opens the draft, sees:
   - SKU, warehouse, current stock vs reorder point
   - Suggested supplier (with on-time rate, lead time, unit price)
   - Suggested quantity + reasoning ("covers 30 days demand at current velocity")
   - Alternative suppliers (one-click swap)
   - Editable quantity / supplier / notes
5. Buttons: **Place PO**, **Edit & Place**, **Reject**, **Snooze 24h**.
6. On approval → POST to backend, which submits to supplier system; status moves to "Placed" and the row disappears from the inbox.

## What Lovable Builds (Frontend)

### New section: Procurement Inbox
File: `src/components/dashboard/procurement-inbox.tsx`
- Lives inside the existing `SuppliersSection` or as its own section above it.
- Lists pending draft POs as cards. Each card shows trigger reason, suggested supplier, qty, total cost, and action buttons.
- Uses the same status color scheme (red = critical/urgent, amber = warning, green = healthy supplier).

### Draft PO review modal
File: `src/components/dashboard/po-review-dialog.tsx`
- Opens on card click.
- Shows full draft with editable fields (qty, supplier dropdown, notes).
- Shows AI rationale block ("Why this supplier? Why this quantity?") returned from backend.
- Footer: Reject · Snooze · Edit & Place · Place PO.

### Data + API additions
- `src/lib/types.ts`: add `DraftPO`, `PlacedPO`, `POStatus` types.
- `src/lib/mock-data.ts`: mock 3-4 draft POs so the UI is demoable before backend is wired.
- `src/lib/api.ts`: new methods
  - `api.draftPOs()` → GET `/po/drafts`
  - `api.placePO(id, overrides)` → POST `/po/drafts/:id/place`
  - `api.rejectPO(id, reason)` → POST `/po/drafts/:id/reject`
  - `api.snoozePO(id, hours)` → POST `/po/drafts/:id/snooze`
  - `api.placedPOs()` → GET `/po/placed` (history table)
- `src/lib/api-config.ts`: document new endpoints in the contract comment.

### Kafka stream extension
- `src/hooks/use-kafka-stream.ts`: add `"po_drafts"` and `"po_placed"` event types so the inbox auto-refreshes the moment your backend creates a new draft.
- `src/routes/index.tsx`: register `po_drafts` in the flash + invalidate map so the new section pulses on update.

### History view
- Small "Recently Placed POs" table below the inbox showing PO #, supplier, qty, status (Submitted / Acknowledged / Shipped), placed by (user), placed at.

### AI assistant integration
- Chat panel already exists. Add a suggested prompt chip: *"Why did you draft PO-1042?"* — backend AI agent already has the data, no new wiring needed.

## What You Build (Backend) — out of scope for Lovable but documented

Lovable cannot touch your Postgres / Kafka / agents, so here's the contract the frontend expects:

1. **Reorder rule engine** (Python/whatever): on each inventory Kafka event, evaluate `onHand <= reorderPoint`. If true and no open draft/placed PO exists for that SKU, create a draft.
2. **Supplier scoring**: pick supplier by composite score (on-time rate × price × lead time × current capacity). Store rationale as text.
3. **Quantity logic**: economic order quantity, or simply `target_days_of_cover * avg_daily_demand`.
4. **New tables / MVs**: `po_drafts`, `po_placed`, `po_audit_log`.
5. **REST endpoints**: the 5 listed above. JSON shapes will match the TS types Lovable defines — share them and we'll keep them in sync.
6. **WebSocket events**: emit `{type:"po_drafts"}` when a new draft is created or status changes; `{type:"po_placed"}` after a successful supplier submission.
7. **Place PO handler**: when frontend POSTs to `/po/drafts/:id/place`, your backend submits to the supplier (EDI / email / API), records the user, and emits both events.

## Safety Rails (recommended)

- **Auto-place threshold**: optional — POs under $X with a trusted supplier can skip approval. UI shows them in a separate "Auto-placed" tab. Off by default.
- **Daily spend cap**: backend refuses to draft beyond a configurable daily $ limit; surplus drafts queue.
- **Duplicate guard**: never draft a second PO for a SKU that already has an open draft or unfulfilled placed PO.
- **Audit log**: every action (drafted, edited, approved, rejected, snoozed, auto-placed) recorded with user + timestamp — visible in the PO detail modal.

## Files Lovable Will Create / Edit

- create `src/components/dashboard/procurement-inbox.tsx`
- create `src/components/dashboard/po-review-dialog.tsx`
- edit `src/lib/types.ts` (add PO types)
- edit `src/lib/mock-data.ts` (mock drafts)
- edit `src/lib/api.ts` (new endpoints + mock fallbacks)
- edit `src/lib/api-config.ts` (document contract)
- edit `src/hooks/use-kafka-stream.ts` (new event types)
- edit `src/routes/index.tsx` (mount inbox section)

Approve this and I'll build the frontend with mock data first so you can see the full flow, then you wire your backend to the documented contract.
