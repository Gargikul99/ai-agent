import type {
  DraftPO,
  InventorySnapshot,
  OrdersSnapshot,
  PODraftsSnapshot,
  PlacedPO,
  ShipmentsSnapshot,
  SuppliersSnapshot,
} from "./types";

const now = () => new Date().toISOString();

// Slight randomization so refreshes are visible
const j = (n: number, spread = 0.08) =>
  Math.round(n * (1 + (Math.random() - 0.5) * spread));

export const mockInventory = (): InventorySnapshot => ({
  updatedAt: now(),
  kpis: [
    { label: "Total SKUs", value: j(12480), status: "healthy" },
    { label: "Low Stock", value: j(34), delta: "+3", status: "warning" },
    { label: "Out of Stock", value: j(7), delta: "+1", status: "critical" },
    { label: "Stock Value", value: `$${j(2_840_000).toLocaleString()}`, status: "healthy" },
  ],
  lowStock: [
    { sku: "SKU-1042", name: "Cobalt Resistor 10k", warehouse: "WH-A Mumbai", onHand: 12, reorderPoint: 50, status: "critical" },
    { sku: "SKU-2891", name: "PCB v3 Board", warehouse: "WH-B Berlin", onHand: 38, reorderPoint: 80, status: "warning" },
    { sku: "SKU-0773", name: "Lithium Cell 18650", warehouse: "WH-C Austin", onHand: 0, reorderPoint: 200, status: "critical" },
    { sku: "SKU-5520", name: "Aluminum Casing M", warehouse: "WH-A Mumbai", onHand: 65, reorderPoint: 100, status: "warning" },
    { sku: "SKU-9981", name: "Cooling Fan 80mm", warehouse: "WH-D Singapore", onHand: 144, reorderPoint: 150, status: "warning" },
  ],
  byWarehouse: [
    { warehouse: "Mumbai", units: j(48000) },
    { warehouse: "Berlin", units: j(32000) },
    { warehouse: "Austin", units: j(27500) },
    { warehouse: "Singapore", units: j(41200) },
  ],
});

export const mockShipments = (): ShipmentsSnapshot => ({
  updatedAt: now(),
  kpis: [
    { label: "In Transit", value: j(218), status: "healthy" },
    { label: "On Time", value: `${j(91)}%`, status: "healthy" },
    { label: "Delayed", value: j(17), delta: "+4", status: "warning" },
    { label: "Critical Delays", value: j(3), status: "critical" },
  ],
  inTransit: (() => {
    const routes: Array<{
      id: string; origin: string; destination: string; carrier: string;
      eta: string; status: "healthy" | "warning" | "critical"; delayHours: number;
      originCoords: [number, number]; destinationCoords: [number, number];
    }> = [
      { id: "SH-88421", origin: "Shanghai", destination: "Rotterdam", carrier: "Maersk", eta: "2026-05-04", status: "healthy", delayHours: 0, originCoords: [31.23, 121.47], destinationCoords: [51.92, 4.48] },
      { id: "SH-88422", origin: "Mumbai", destination: "Hamburg", carrier: "MSC", eta: "2026-05-06", status: "warning", delayHours: 12, originCoords: [19.07, 72.87], destinationCoords: [53.55, 9.99] },
      { id: "SH-88423", origin: "Los Angeles", destination: "Tokyo", carrier: "ONE", eta: "2026-05-03", status: "critical", delayHours: 36, originCoords: [33.74, -118.27], destinationCoords: [35.68, 139.76] },
      { id: "SH-88424", origin: "Dubai", destination: "Mumbai", carrier: "CMA CGM", eta: "2026-05-02", status: "healthy", delayHours: 0, originCoords: [25.27, 55.30], destinationCoords: [19.07, 72.87] },
      { id: "SH-88425", origin: "Singapore", destination: "Sydney", carrier: "Evergreen", eta: "2026-05-05", status: "warning", delayHours: 8, originCoords: [1.35, 103.82], destinationCoords: [-33.87, 151.21] },
    ];
    return routes.map((r) => {
      const progress = Math.random() * 0.8 + 0.1;
      const lat = r.originCoords[0] + (r.destinationCoords[0] - r.originCoords[0]) * progress;
      const lng = r.originCoords[1] + (r.destinationCoords[1] - r.originCoords[1]) * progress;
      return { ...r, lat, lng, progress };
    });
  })(),
  byStatus: [
    { status: "On Time", count: j(184) },
    { status: "Delayed", count: j(17) },
    { status: "Critical", count: j(3) },
    { status: "Delivered Today", count: j(42) },
  ],
});

export const mockOrders = (): OrdersSnapshot => ({
  updatedAt: now(),
  kpis: [
    { label: "Orders Today", value: j(1284), delta: "+8%", status: "healthy" },
    { label: "Fulfillment Rate", value: `${j(96)}%`, status: "healthy" },
    { label: "Backorders", value: j(43), delta: "+5", status: "warning" },
    { label: "Cancelled", value: j(11), status: "critical" },
  ],
  recent: [
    { id: "ORD-77231", customer: "Acme Industries", items: 12, value: 4820, status: "healthy", placedAt: "10:42" },
    { id: "ORD-77232", customer: "Globex Corp", items: 3, value: 1290, status: "warning", placedAt: "10:39" },
    { id: "ORD-77233", customer: "Initech Ltd", items: 28, value: 12480, status: "healthy", placedAt: "10:35" },
    { id: "ORD-77234", customer: "Soylent Co", items: 7, value: 2110, status: "critical", placedAt: "10:31" },
    { id: "ORD-77235", customer: "Umbrella Corp", items: 4, value: 980, status: "healthy", placedAt: "10:28" },
  ],
  fulfillmentTrend: Array.from({ length: 12 }).map((_, i) => ({
    hour: `${i * 2}:00`,
    orders: j(80 + i * 4, 0.2),
    fulfilled: j(74 + i * 4, 0.2),
  })),
});

export const mockSuppliers = (): SuppliersSnapshot => ({
  updatedAt: now(),
  kpis: [
    { label: "Active Suppliers", value: j(142), status: "healthy" },
    { label: "Avg Lead Time", value: `${j(11)}d`, status: "warning" },
    { label: "Open POs", value: j(287), status: "healthy" },
    { label: "At Risk", value: j(6), status: "critical" },
  ],
  suppliers: [
    { id: "SUP-001", name: "Shenzhen Electronics", region: "APAC", onTimeRate: 0.97, leadTimeDays: 8, status: "healthy" },
    { id: "SUP-002", name: "Bavaria Precision", region: "EMEA", onTimeRate: 0.92, leadTimeDays: 14, status: "healthy" },
    { id: "SUP-003", name: "TexMex Components", region: "AMER", onTimeRate: 0.78, leadTimeDays: 21, status: "warning" },
    { id: "SUP-004", name: "Nordic Steel AB", region: "EMEA", onTimeRate: 0.61, leadTimeDays: 28, status: "critical" },
    { id: "SUP-005", name: "Pacific Polymers", region: "APAC", onTimeRate: 0.95, leadTimeDays: 10, status: "healthy" },
  ],
});

// In-memory mutable PO store so accept/reject actions feel real in mock mode
const initialDrafts: DraftPO[] = [
  {
    id: "PO-DRAFT-1042",
    sku: "SKU-1042",
    productName: "Cobalt Resistor 10k",
    warehouse: "WH-A Mumbai",
    onHand: 12,
    reorderPoint: 50,
    avgDailyDemand: 22,
    suggestedQty: 660,
    suggestedSupplier: {
      supplierId: "SUP-001",
      supplierName: "Shenzhen Electronics",
      unitPrice: 0.42,
      leadTimeDays: 8,
      onTimeRate: 0.97,
      score: 0.94,
    },
    alternativeSuppliers: [
      { supplierId: "SUP-005", supplierName: "Pacific Polymers", unitPrice: 0.45, leadTimeDays: 10, onTimeRate: 0.95, score: 0.88 },
      { supplierId: "SUP-003", supplierName: "TexMex Components", unitPrice: 0.38, leadTimeDays: 21, onTimeRate: 0.78, score: 0.66 },
    ],
    unitPrice: 0.42,
    totalCost: 277.2,
    estimatedEta: "2026-05-12",
    rationale:
      "Stock at 12 vs reorder 50 — critical. Suggested 660 units = 30 days cover at avg 22/day. Shenzhen Electronics scored highest (97% on-time, 8d lead, $0.42/unit).",
    urgency: "critical",
    createdAt: now(),
    status: "pending_approval",
  },
  {
    id: "PO-DRAFT-0773",
    sku: "SKU-0773",
    productName: "Lithium Cell 18650",
    warehouse: "WH-C Austin",
    onHand: 0,
    reorderPoint: 200,
    avgDailyDemand: 85,
    suggestedQty: 2550,
    suggestedSupplier: {
      supplierId: "SUP-005",
      supplierName: "Pacific Polymers",
      unitPrice: 3.10,
      leadTimeDays: 10,
      onTimeRate: 0.95,
      score: 0.91,
    },
    alternativeSuppliers: [
      { supplierId: "SUP-001", supplierName: "Shenzhen Electronics", unitPrice: 3.25, leadTimeDays: 8, onTimeRate: 0.97, score: 0.89 },
    ],
    unitPrice: 3.10,
    totalCost: 7905,
    estimatedEta: "2026-05-14",
    rationale:
      "STOCKOUT — 0 units on hand. Expedite recommended. 2550 units = 30 days cover. Pacific Polymers offers best balance of price and reliability.",
    urgency: "critical",
    createdAt: now(),
    status: "pending_approval",
  },
  {
    id: "PO-DRAFT-2891",
    sku: "SKU-2891",
    productName: "PCB v3 Board",
    warehouse: "WH-B Berlin",
    onHand: 38,
    reorderPoint: 80,
    avgDailyDemand: 9,
    suggestedQty: 270,
    suggestedSupplier: {
      supplierId: "SUP-002",
      supplierName: "Bavaria Precision",
      unitPrice: 12.40,
      leadTimeDays: 14,
      onTimeRate: 0.92,
      score: 0.86,
    },
    alternativeSuppliers: [
      { supplierId: "SUP-001", supplierName: "Shenzhen Electronics", unitPrice: 11.20, leadTimeDays: 22, onTimeRate: 0.97, score: 0.79 },
    ],
    unitPrice: 12.40,
    totalCost: 3348,
    estimatedEta: "2026-05-18",
    rationale:
      "Below reorder point. Local EMEA supplier preferred to minimize lead time given Berlin warehouse location.",
    urgency: "warning",
    createdAt: now(),
    status: "pending_approval",
  },
  {
    id: "PO-DRAFT-5520",
    sku: "SKU-5520",
    productName: "Aluminum Casing M",
    warehouse: "WH-A Mumbai",
    onHand: 65,
    reorderPoint: 100,
    avgDailyDemand: 6,
    suggestedQty: 180,
    suggestedSupplier: {
      supplierId: "SUP-001",
      supplierName: "Shenzhen Electronics",
      unitPrice: 4.80,
      leadTimeDays: 8,
      onTimeRate: 0.97,
      score: 0.92,
    },
    alternativeSuppliers: [],
    unitPrice: 4.80,
    totalCost: 864,
    estimatedEta: "2026-05-12",
    rationale: "Stock approaching reorder point. Standard restock.",
    urgency: "warning",
    createdAt: now(),
    status: "pending_approval",
  },
];

const placedHistory: PlacedPO[] = [
  { id: "PO-10039", sku: "SKU-3344", productName: "Rubber Gasket S", supplierName: "Pacific Polymers", qty: 1200, totalCost: 540, status: "shipped", placedBy: "a.kumar", placedAt: "2026-05-03 14:22" },
  { id: "PO-10040", sku: "SKU-7711", productName: "Copper Wire 2mm", supplierName: "Shenzhen Electronics", qty: 800, totalCost: 1920, status: "acknowledged", placedBy: "j.smith", placedAt: "2026-05-04 08:15" },
  { id: "PO-10041", sku: "SKU-4422", productName: "Steel Bracket L", supplierName: "Bavaria Precision", qty: 350, totalCost: 2625, status: "placed", placedBy: "a.kumar", placedAt: "2026-05-04 10:01" },
];

const draftStore: DraftPO[] = [...initialDrafts];

export const mockPODrafts = (): PODraftsSnapshot => {
  const pending = draftStore.filter((d) => d.status === "pending_approval");
  const totalValue = pending.reduce((s, d) => s + d.totalCost, 0);
  const critical = pending.filter((d) => d.urgency === "critical").length;
  return {
    updatedAt: now(),
    drafts: pending,
    placed: placedHistory,
    kpis: [
      { label: "Awaiting Approval", value: pending.length, status: pending.length > 0 ? "warning" : "healthy" },
      { label: "Critical Drafts", value: critical, status: critical > 0 ? "critical" : "healthy" },
      { label: "Pending Spend", value: `$${Math.round(totalValue).toLocaleString()}`, status: "healthy" },
      { label: "Placed Today", value: placedHistory.length, status: "healthy" },
    ],
  };
};

export const mockPlacePO = (id: string, overrides?: { qty?: number; supplierId?: string }) => {
  const draft = draftStore.find((d) => d.id === id);
  if (!draft) throw new Error("Draft not found");
  const qty = overrides?.qty ?? draft.suggestedQty;
  const supplier = overrides?.supplierId
    ? [draft.suggestedSupplier, ...draft.alternativeSuppliers].find((s) => s.supplierId === overrides.supplierId) ?? draft.suggestedSupplier
    : draft.suggestedSupplier;
  draft.status = "placed";
  placedHistory.unshift({
    id: `PO-${10042 + placedHistory.length}`,
    sku: draft.sku,
    productName: draft.productName,
    supplierName: supplier.supplierName,
    qty,
    totalCost: Math.round(qty * supplier.unitPrice * 100) / 100,
    status: "placed",
    placedBy: "you",
    placedAt: new Date().toLocaleString(),
  });
};

export const mockRejectPO = (id: string) => {
  const draft = draftStore.find((d) => d.id === id);
  if (draft) draft.status = "rejected";
};

export const mockSnoozePO = (id: string) => {
  const draft = draftStore.find((d) => d.id === id);
  if (draft) draft.status = "snoozed";
};
