"use client";

import { useEffect, useState } from "react";

import { procurementApi } from "@/lib/procurement-api";
import type { DashboardMetrics } from "@/types/procurement";

type DashboardMetricsState =
  | { status: "loading" }
  | { status: "success"; data: DashboardMetrics }
  | { status: "error"; message: string };

export function useDashboardMetrics() {
  const [state, setState] = useState<DashboardMetricsState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    procurementApi
      .getDashboardMetrics()
      .then((data) => {
        if (!cancelled) setState({ status: "success", data });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        const message = error instanceof Error ? error.message : "Failed to load metrics";
        setState({ status: "error", message });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
