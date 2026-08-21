"use client";

import { useEffect, useState } from "react";
import {
  Boxes,
  CheckCircle2,
  FileSearch,
  FileText,
  Package,
  PackageCheck,
  ShieldAlert,
  ShoppingCart,
  Sparkles,
  Upload,
  Wallet,
  XCircle,
  type LucideIcon,
} from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { procurementApi } from "@/lib/procurement-api";
import type { AuditEvent, AuditEventType } from "@/types/procurement";

const EVENT_ICON: Record<AuditEventType, LucideIcon> = {
  rfq_created: FileText,
  quote_uploaded: Upload,
  quote_analyzed: FileSearch,
  quote_extraction_failed: XCircle,
  risk_detected: ShieldAlert,
  recommendation_generated: Sparkles,
  rfq_approved: CheckCircle2,
  rfq_rejected: XCircle,
  po_created: ShoppingCart,
  po_issued: Package,
  po_acknowledged: PackageCheck,
  po_received: Boxes,
  po_cancelled: XCircle,
  inventory_received: Boxes,
  finance_transaction_created: Wallet,
};

const EVENT_COLOR: Record<AuditEventType, string> = {
  rfq_created: "text-muted-foreground",
  quote_uploaded: "text-sky-600 dark:text-sky-400",
  quote_analyzed: "text-intelligence",
  quote_extraction_failed: "text-destructive",
  risk_detected: "text-amber-600 dark:text-amber-400",
  recommendation_generated: "text-intelligence",
  rfq_approved: "text-emerald-600 dark:text-emerald-400",
  rfq_rejected: "text-destructive",
  po_created: "text-amber-600 dark:text-amber-400",
  po_issued: "text-emerald-700 dark:text-emerald-300",
  po_acknowledged: "text-sky-600 dark:text-sky-400",
  po_received: "text-violet-600 dark:text-violet-400",
  po_cancelled: "text-destructive",
  inventory_received: "text-violet-600 dark:text-violet-400",
  finance_transaction_created: "text-emerald-600 dark:text-emerald-400",
};

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

type State =
  | { status: "loading" }
  | { status: "success"; items: AuditEvent[] }
  | { status: "error"; message: string };

export function AuditTimeline({ rfqId }: { rfqId: string }) {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    procurementApi
      .getAuditTrail(rfqId)
      .then((res) => {
        if (!cancelled) setState({ status: "success", items: res.items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Failed to load activity";
        setState({ status: "error", message });
      });

    return () => {
      cancelled = true;
    };
  }, [rfqId]);

  if (state.status === "loading") {
    return (
      <div className="space-y-3">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }

  if (state.status === "error") {
    return <p className="text-sm text-destructive">{state.message}</p>;
  }

  if (state.items.length === 0) {
    return (
      <p className="py-4 text-sm text-muted-foreground">
        No activity recorded yet. Every step of this RFQ&apos;s lifecycle will show up here.
      </p>
    );
  }

  return (
    <ol className="relative space-y-5 border-l border-border pl-5">
      {state.items.map((event) => {
        const Icon = EVENT_ICON[event.event_type] ?? FileText;
        return (
          <li key={event.id} className="relative">
            <span
              className={`absolute top-0.5 -left-[1.6rem] flex h-6 w-6 items-center justify-center rounded-full border border-border bg-background ${EVENT_COLOR[event.event_type] ?? "text-muted-foreground"}`}
            >
              <Icon className="h-3.5 w-3.5" />
            </span>
            <p className="text-sm font-medium">{event.description}</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {formatTimestamp(event.created_at)}
              {event.actor ? ` · ${event.actor}` : ""}
            </p>
          </li>
        );
      })}
    </ol>
  );
}
