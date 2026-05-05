import { useEffect, useRef, useState } from "react";
import { API_CONFIG, type SectionKey } from "@/lib/api-config";

export type StreamStatus = "connecting" | "live" | "offline" | "mock";

interface KafkaEvent {
  type: SectionKey | "all";
}

/**
 * Subscribes to the Kafka push WebSocket and calls onEvent with the section
 * to refetch. In mock mode it emits synthetic events on a timer so you can
 * see the dashboard react.
 */
export function useKafkaStream(onEvent: (section: SectionKey | "all") => void) {
  const [status, setStatus] = useState<StreamStatus>(
    API_CONFIG.USE_MOCK ? "mock" : "connecting",
  );
  const [lastEventAt, setLastEventAt] = useState<Date | null>(null);
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;

  useEffect(() => {
    // Mock mode: emit a random section update every 8s
    if (API_CONFIG.USE_MOCK) {
      const sections: (SectionKey | "all")[] = [
        "inventory",
        "shipments",
        "orders",
        "suppliers",
        "po_drafts",
      ];
      const id = setInterval(() => {
        const s = sections[Math.floor(Math.random() * sections.length)];
        setLastEventAt(new Date());
        handlerRef.current(s);
      }, 8000);
      return () => clearInterval(id);
    }

    let ws: WebSocket | null = null;
    let retry: ReturnType<typeof setTimeout> | null = null;
    let closed = false;

    const connect = () => {
      try {
        ws = new WebSocket(API_CONFIG.WS_URL);
        setStatus("connecting");
        ws.onopen = () => setStatus("live");
        ws.onclose = () => {
          setStatus("offline");
          if (!closed) retry = setTimeout(connect, 3000);
        };
        ws.onerror = () => setStatus("offline");
        ws.onmessage = (msg) => {
          try {
            const data: KafkaEvent = JSON.parse(msg.data);
            setLastEventAt(new Date());
            handlerRef.current(data.type ?? "all");
          } catch {
            handlerRef.current("all");
          }
        };
      } catch {
        setStatus("offline");
        if (!closed) retry = setTimeout(connect, 3000);
      }
    };
    connect();

    return () => {
      closed = true;
      if (retry) clearTimeout(retry);
      ws?.close();
    };
  }, []);

  return { status, lastEventAt };
}
