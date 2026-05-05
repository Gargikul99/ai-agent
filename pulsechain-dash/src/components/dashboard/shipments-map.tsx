import { useEffect, useRef } from "react";
import type { Shipment } from "@/lib/types";

const STATUS_COLOR: Record<string, string> = {
  healthy: "#4ade80",
  warning: "#facc15",
  critical: "#f87171",
};

export function ShipmentsMap({ shipments }: { shipments: Shipment[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const layerRef = useRef<any>(null);
  const LRef = useRef<any>(null);

  // Init map (client-only)
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const L = await import("leaflet");
      await import("leaflet/dist/leaflet.css");
      if (cancelled || !containerRef.current || mapRef.current) return;
      LRef.current = L;
      const map = L.map(containerRef.current, {
      center: [39.5, -98.35],  // ← center of USA
      zoom: 4,                  // ← zoom in to see US
      worldCopyJump: true,
      zoomControl: true,
      attributionControl: false,
    });
      L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        { maxZoom: 8, minZoom: 2 },
      ).addTo(map);
      mapRef.current = map;
      layerRef.current = L.layerGroup().addTo(map);
    })();
    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  // Render markers/routes when shipments change
  useEffect(() => {
    // Wait for map to be ready
    const renderMarkers = () => {
      const L = LRef.current;
      const layer = layerRef.current;
      if (!L || !layer) {
        setTimeout(renderMarkers, 100); // retry until map is ready
        return;
      }
      layer.clearLayers();
      shipments.forEach((s) => {
        if (!s.originCoords || !s.destinationCoords || 
            s.lat == null || s.lng == null) return;
        const color = STATUS_COLOR[s.status] ?? "#94a3b8";
        L.polyline([s.originCoords, s.destinationCoords], {
        color,
        weight: 3,
        opacity: 0.6,
        dashArray: "4 6",
      }).bindTooltip(
        `<strong>${s.id}</strong><br/>${s.origin} → ${s.destination}<br/>${s.carrier}${s.delayHours > 0 ? ` · +${s.delayHours}h delay` : ""}`,
        { direction: "top", sticky: true }
      ).addTo(layer);
        L.circleMarker(s.originCoords, {
          radius: 3, color: "#cbd5e1", fillColor: "#cbd5e1", 
          fillOpacity: 0.8, weight: 0,
        }).addTo(layer);
        L.circleMarker(s.destinationCoords, {
          radius: 3, color: "#cbd5e1", fillColor: "#cbd5e1", 
          fillOpacity: 0.8, weight: 0,
        }).addTo(layer);
        L.circleMarker([s.lat, s.lng], {
        radius: 6, color, fillColor: color, fillOpacity: 0.9, weight: 2,
          })
          .bindTooltip(
            `<strong>${s.id}</strong><br/>${s.origin} → ${s.destination}<br/>${s.carrier} · ${Math.round((s.progress ?? 0) * 100)}%${s.delayHours > 0 ? ` · +${s.delayHours}h` : ""}`,
            { direction: "top", offset: [0, -6] },
          )
          .addTo(layer);
      });
    };
    renderMarkers();
  }, [shipments]);

  return (
    <div
      ref={containerRef}
      className="w-full h-[320px] rounded-md overflow-hidden ring-1 ring-border/40 bg-background/40"
      style={{ zIndex: 0 }}
    />
  );
}

export default ShipmentsMap;
