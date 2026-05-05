export type HealthStatus = "healthy" | "warning" | "critical";

export interface KpiTile {
  label: string;
  value: string | number;
  delta?: string;
  status: HealthStatus;
}

export interface InventoryItem {
  sku: string;
  name: string;
  warehouse: string;
  onHand: number;
  reorderPoint: number;
  status: HealthStatus;
}
export interface InventorySnapshot {
  kpis: KpiTile[];
  lowStock: InventoryItem[];
  byWarehouse: { warehouse: string; units: number }[];
  updatedAt: string;
}

export interface Shipment {
  id: string;
  origin: string;
  destination: string;
  carrier: string;
  eta: string;
  status: HealthStatus;
  delayHours: number;
  // Live position for map tracking
  lat?: number;
  lng?: number;
  originCoords?: [number, number];
  destinationCoords?: [number, number];
  progress?: number; // 0-1
}
export interface ShipmentsSnapshot {
  kpis: KpiTile[];
  inTransit: Shipment[];
  byStatus: { status: string; count: number }[];
  updatedAt: string;
}

export interface OrderRow {
  id: string;
  customer: string;
  items: number;
  value: number;
  status: HealthStatus;
  placedAt: string;
}
export interface OrdersSnapshot {
  kpis: KpiTile[];
  recent: OrderRow[];
  fulfillmentTrend: { hour: string; orders: number; fulfilled: number }[];
  updatedAt: string;
}

export interface SupplierRow {
  id: string;
  name: string;
  region: string;
  onTimeRate: number; // 0-1
  leadTimeDays: number;
  status: HealthStatus;
}
export interface SuppliersSnapshot {
  kpis: KpiTile[];
  suppliers: SupplierRow[];
  updatedAt: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export type POStatus =
  | "pending_approval"
  | "placed"
  | "acknowledged"
  | "shipped"
  | "rejected"
  | "snoozed";

export interface SupplierOption {
  supplierId: string;
  supplierName: string;
  unitPrice: number;
  leadTimeDays: number;
  onTimeRate: number;
  score: number; // 0-1, higher better
}

export interface DraftPO {
  id: string;
  sku: string;
  productName: string;
  warehouse: string;
  onHand: number;
  reorderPoint: number;
  avgDailyDemand: number;
  suggestedQty: number;
  suggestedSupplier: SupplierOption;
  alternativeSuppliers: SupplierOption[];
  unitPrice: number;
  totalCost: number;
  estimatedEta: string;
  rationale: string;
  urgency: HealthStatus;
  createdAt: string;
  status: POStatus;
}

export interface PlacedPO {
  id: string;
  sku: string;
  productName: string;
  supplierName: string;
  qty: number;
  totalCost: number;
  status: POStatus;
  placedBy: string;
  placedAt: string;
}

export interface PODraftsSnapshot {
  drafts: DraftPO[];
  placed: PlacedPO[];
  kpis: KpiTile[];
  updatedAt: string;
}
