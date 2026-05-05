export const API_CONFIG = {
  USE_MOCK: false, // ← switched to real data

  REST_BASE: "http://localhost:8000/api",
  AI_AGENT_URL: "http://localhost:8000/api/chat",
  WS_URL: "ws://localhost:8000/ws",
} as const;

export type SectionKey =
  | "inventory"
  | "shipments"
  | "orders"
  | "suppliers"
  | "po_drafts";

export const ALL_SECTIONS: SectionKey[] = [
  "inventory",
  "shipments",
  "orders",
  "suppliers",
  "po_drafts",
];