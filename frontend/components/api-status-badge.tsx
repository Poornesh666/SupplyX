"use client";

import { Badge } from "@/components/ui/badge";
import { useHealth } from "@/hooks/use-health";

export function ApiStatusBadge() {
  const health = useHealth();

  if (health.status === "loading") {
    return (
      <Badge variant="outline" className="gap-1.5 text-muted-foreground">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground" />
        Connecting to API
      </Badge>
    );
  }

  if (health.status === "error") {
    return (
      <Badge variant="outline" className="gap-1.5 border-destructive/40 text-destructive">
        <span className="h-1.5 w-1.5 rounded-full bg-destructive" />
        API offline
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className="gap-1.5 border-emerald-500/40 text-emerald-600 dark:text-emerald-400">
      <span className="relative flex h-1.5 w-1.5">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-75 motion-reduce:animate-none" />
        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
      </span>
      AI Engine Online
      {!health.data.database_connected && " · DB offline"}
    </Badge>
  );
}
