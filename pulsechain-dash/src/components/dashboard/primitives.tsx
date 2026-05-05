import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { HealthStatus, KpiTile } from "@/lib/types";

const statusRing: Record<HealthStatus, string> = {
  healthy: "ring-[color:var(--status-healthy)]/40",
  warning: "ring-[color:var(--status-warning)]/40",
  critical: "ring-[color:var(--status-critical)]/50",
};
const statusText: Record<HealthStatus, string> = {
  healthy: "text-[color:var(--status-healthy)]",
  warning: "text-[color:var(--status-warning)]",
  critical: "text-[color:var(--status-critical)]",
};
const statusDot: Record<HealthStatus, string> = {
  healthy: "bg-[color:var(--status-healthy)]",
  warning: "bg-[color:var(--status-warning)]",
  critical: "bg-[color:var(--status-critical)]",
};

export function KpiGrid({ tiles }: { tiles: KpiTile[] }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {tiles.map((t) => {
        const s = (t.status ?? "healthy") as HealthStatus;
        return (
          <Card
            key={t.label}
            className={cn(
              "p-4 ring-1 ring-inset bg-card text-card-foreground border-border/40",
              statusRing[s],
            )}
          >
            <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-muted-foreground">
              <span className={cn("h-2 w-2 rounded-full", statusDot[s])} />
              {t.label}
            </div>
            <div className="mt-2 text-2xl font-semibold">{t.value}</div>
            {t.delta && (
              <div className={cn("mt-1 text-xs", statusText[s])}>{t.delta}</div>
            )}
          </Card>
        );
      })}
    </div>
  );
}

export function StatusPill({ status }: { status: HealthStatus }) {
  const labels: Record<HealthStatus, string> = {
    healthy: "Healthy",
    warning: "Warning",
    critical: "Critical",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        statusRing[status],
        statusText[status],
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", statusDot[status])} />
      {labels[status]}
    </span>
  );
}

export function SectionCard({
  title,
  subtitle,
  flash,
  children,
}: {
  title: string;
  subtitle?: string;
  flash?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Card
      className={cn(
        "p-5 bg-card text-card-foreground border-border/40 transition-shadow",
        flash && "ring-2 ring-primary/60 shadow-[0_0_0_4px_var(--primary)]/20",
      )}
    >
      <div className="mb-4 flex items-baseline justify-between">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          {subtitle && (
            <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
          )}
        </div>
      </div>
      {children}
    </Card>
  );
}
