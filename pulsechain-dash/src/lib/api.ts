import { API_CONFIG } from "./api-config";
import {
  mockInventory,
  mockOrders,
  mockPODrafts,
  mockPlacePO,
  mockRejectPO,
  mockShipments,
  mockSnoozePO,
  mockSuppliers,
} from "./mock-data";
import type {
  ChatMessage,
  InventorySnapshot,
  OrdersSnapshot,
  PODraftsSnapshot,
  ShipmentsSnapshot,
  SuppliersSnapshot,
} from "./types";

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_CONFIG.REST_BASE}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return (await res.json()) as T;
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_CONFIG.REST_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return (await res.json()) as T;
}

export const api = {
  inventory: (): Promise<InventorySnapshot> =>
    API_CONFIG.USE_MOCK ? Promise.resolve(mockInventory()) : getJSON("/inventory"),
  shipments: (): Promise<ShipmentsSnapshot> =>
    API_CONFIG.USE_MOCK ? Promise.resolve(mockShipments()) : getJSON("/shipments"),
  orders: (): Promise<OrdersSnapshot> =>
    API_CONFIG.USE_MOCK ? Promise.resolve(mockOrders()) : getJSON("/orders"),
  suppliers: (): Promise<SuppliersSnapshot> =>
    API_CONFIG.USE_MOCK ? Promise.resolve(mockSuppliers()) : getJSON("/suppliers"),

  poDrafts: (): Promise<PODraftsSnapshot> =>
    API_CONFIG.USE_MOCK ? Promise.resolve(mockPODrafts()) : getJSON("/po/drafts"),

  placePO: async (id: string, overrides?: { qty?: number; supplierId?: string }) => {
    if (API_CONFIG.USE_MOCK) { mockPlacePO(id, overrides); return { ok: true }; }
    return postJSON(`/po/drafts/${id}/place`, overrides ?? {});
  },
  rejectPO: async (id: string, reason?: string) => {
    if (API_CONFIG.USE_MOCK) { mockRejectPO(id); return { ok: true }; }
    return postJSON(`/po/drafts/${id}/reject`, { reason });
  },
  snoozePO: async (id: string, hours = 24) => {
    if (API_CONFIG.USE_MOCK) { mockSnoozePO(id); return { ok: true }; }
    return postJSON(`/po/drafts/${id}/snooze`, { hours });
  },

  async chat(messages: ChatMessage[]): Promise<string> {
    if (API_CONFIG.USE_MOCK) {
      await new Promise((r) => setTimeout(r, 600));
      const last = messages[messages.length - 1]?.content ?? "";
      return [
        `**Mock AI response.** Wire up \`API_CONFIG.AI_AGENT_URL\` to use your real agent.`,
        ``,
        `You asked: _${last}_`,
        ``,
        `Once connected, I can answer queries like:`,
        `- *"Which suppliers are at risk this week?"*`,
        `- *"Show me SKUs below reorder point in Mumbai"*`,
        `- *"What's the average shipment delay from Shanghai?"*`,
      ].join("\n");
    }
    const res = await fetch(API_CONFIG.AI_AGENT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });
    if (!res.ok) throw new Error(`chat -> ${res.status}`);
    const data = await res.json();
    return data.reply ?? data.content ?? data.message ?? "";
  },
};
