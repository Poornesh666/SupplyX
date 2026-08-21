"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ClipboardList,
  FileSearch,
  ShieldAlert,
  TrendingUp,
  Hourglass,
  ArrowRight,
  Lightbulb,
  Gauge,
  Sparkles,
  ShieldQuestion,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Topbar } from "@/components/layout/topbar";
import { PipelineOverview } from "@/components/procurement/pipeline-overview";
import { RFQStatusBadge } from "@/components/procurement/status-badge";
import { useDashboardMetrics } from "@/hooks/use-dashboard-metrics";
import { procurementApi } from "@/lib/procurement-api";
import type { ProcurementInsight, PurchaseOrder, RFQ } from "@/types/procurement";

function ScenePlaceholder() {
  return (
    <div
      aria-hidden
      className="h-72 w-full rounded-2xl bg-[radial-gradient(circle_at_30%_35%,color-mix(in_oklch,var(--muted-foreground)_18%,transparent),transparent_60%),radial-gradient(circle_at_70%_65%,color-mix(in_oklch,var(--primary)_12%,transparent),transparent_55%)] motion-safe:animate-pulse motion-reduce:animate-none sm:h-96"
      style={{ animationDuration: "6s" }}
    />
  );
}

const ProcurementIntelligenceScene = dynamic(
  () =>
    import("@/components/visualization/procurement-intelligence-scene").then(
      (mod) => mod.ProcurementIntelligenceScene
    ),
  { ssr: false, loading: () => <ScenePlaceholder /> }
);

const METRIC_CARDS: {
  key: "active_rfqs" | "quotes_analyzed" | "risks_detected" | "potential_savings" | "pending_approvals";
  label: string;
  icon: typeof ClipboardList;
  hint: string;
  format?: (value: number) => string;
}[] = [
  {
    key: "active_rfqs",
    label: "Active RFQs",
    icon: ClipboardList,
    hint: "In the procurement decision pipeline",
  },
  {
    key: "quotes_analyzed",
    label: "Quotes Analyzed",
    icon: FileSearch,
    hint: "Structured & scored by the AI engine",
  },
  {
    key: "risks_detected",
    label: "Risks Detected",
    icon: ShieldAlert,
    hint: "Surfaced during quote extraction",
  },
  {
    key: "potential_savings",
    label: "Potential Savings",
    icon: TrendingUp,
    hint: "Calculated by deterministic scoring",
    format: (value) => value.toLocaleString(),
  },
  {
    key: "pending_approvals",
    label: "Pending Approvals",
    icon: Hourglass,
    hint: "Recommendations awaiting sign-off",
  },
];

const PIPELINE_STAGES = ["RFQ", "Vendors", "Quotes", "Analysis", "Decision", "PO"];

function MetricsGrid() {
  const metrics = useDashboardMetrics();
  const primary = METRIC_CARDS[0];
  const supporting = METRIC_CARDS.slice(1);

  const primaryValue = metrics.status === "success" ? metrics.data[primary.key] : null;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="lg:col-span-7"
      >
        <Card className="h-full overflow-hidden border-intelligence/20">
          <CardContent className="flex h-full flex-col justify-between gap-6 pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="flex items-center gap-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  <span className="h-1.5 w-1.5 rounded-full bg-intelligence" />
                  {primary.label}
                </p>
                {metrics.status === "loading" && <Skeleton className="mt-2 h-12 w-24" />}
                {metrics.status === "success" && (
                  <p className="mt-1 font-serif text-6xl tabular-nums sm:text-7xl">
                    {primaryValue}
                  </p>
                )}
                {metrics.status === "error" && (
                  <p className="mt-2 text-sm text-muted-foreground">Unavailable</p>
                )}
                <p className="mt-2 text-sm text-muted-foreground">{primary.hint}</p>
              </div>
              <primary.icon className="h-5 w-5 shrink-0 text-intelligence" />
            </div>

            <div className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
              {PIPELINE_STAGES.map((stage, i) => (
                <span key={stage} className="flex items-center gap-1">
                  <span
                    className={i === 0 ? "font-medium text-foreground" : undefined}
                  >
                    {stage}
                  </span>
                  {i < PIPELINE_STAGES.length - 1 && <ArrowRight className="h-3 w-3" />}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-2 gap-4 lg:col-span-5">
        {supporting.map((card, index) => {
          const value = metrics.status === "success" ? metrics.data[card.key] : null;
          const displayValue =
            value === null ? null : card.format ? card.format(value) : value.toLocaleString();

          return (
            <motion.div
              key={card.key}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.08 + index * 0.05, ease: "easeOut" }}
            >
              <Card className="h-full transition-shadow duration-200 hover:shadow-md">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-xs font-medium text-muted-foreground">
                    {card.label}
                  </CardTitle>
                  <card.icon className="h-3.5 w-3.5 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  {metrics.status === "loading" && <Skeleton className="h-7 w-12" />}
                  {metrics.status === "error" && (
                    <div className="text-xs text-muted-foreground">—</div>
                  )}
                  {metrics.status === "success" && (
                    <div className="text-xl font-semibold tabular-nums">{displayValue}</div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

function RecentRFQs() {
  const [rfqs, setRfqs] = useState<RFQ[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    procurementApi
      .listRFQs()
      .then((res) =>
        setRfqs(
          [...res.items]
            .sort((a, b) => (a.created_at < b.created_at ? 1 : -1))
            .slice(0, 5)
        )
      )
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load RFQs"));
  }, []);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>Recent RFQs</CardTitle>
        <Link
          href="/rfqs"
          className="flex items-center gap-1 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          View all
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </CardHeader>
      <CardContent className="space-y-1">
        {error && <p className="text-sm text-destructive">{error}</p>}
        {!error && rfqs === null && (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}
        {rfqs !== null && rfqs.length === 0 && (
          <p className="py-4 text-sm text-muted-foreground">
            No RFQs yet. Create your first RFQ to start the procurement workflow.
          </p>
        )}
        {rfqs !== null && rfqs.length > 0 && (
          <div>
            {rfqs.map((rfq, index) => (
              <motion.div
                key={rfq.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: index * 0.04, ease: "easeOut" }}
              >
                <Link
                  href={`/rfqs/${rfq.id}`}
                  className="flex items-center justify-between gap-4 rounded-lg px-2 py-3 transition-colors hover:bg-muted/50"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{rfq.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {rfq.rfq_number} · {rfq.quantity} {rfq.unit}
                    </p>
                  </div>
                  <RFQStatusBadge status={rfq.status} />
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

const PO_STATUS_STYLE: Record<PurchaseOrder["status"], string> = {
  draft: "border-muted-foreground/30 text-muted-foreground",
  issued: "border-sky-500/40 text-sky-600 dark:text-sky-400",
  acknowledged: "border-violet-500/40 text-violet-600 dark:text-violet-400",
  received: "border-emerald-600/50 text-emerald-700 dark:text-emerald-300",
  cancelled: "border-destructive/40 text-destructive",
};

function RecentPurchaseOrders() {
  const [pos, setPos] = useState<PurchaseOrder[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    procurementApi
      .listPurchaseOrders()
      .then((res) =>
        setPos(
          [...res.items]
            .sort((a, b) => (a.created_at < b.created_at ? 1 : -1))
            .slice(0, 5)
        )
      )
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load purchase orders")
      );
  }, []);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>Recent Purchase Orders</CardTitle>
        <Link
          href="/purchase-orders"
          className="flex items-center gap-1 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          View all
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </CardHeader>
      <CardContent className="space-y-1">
        {error && <p className="text-sm text-destructive">{error}</p>}
        {!error && pos === null && (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        )}
        {pos !== null && pos.length === 0 && (
          <p className="py-4 text-sm text-muted-foreground">
            No purchase orders yet. They appear here once an approved RFQ is converted to a PO.
          </p>
        )}
        {pos !== null && pos.length > 0 && (
          <div>
            {pos.map((po, index) => (
              <motion.div
                key={po.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: index * 0.04, ease: "easeOut" }}
              >
                <Link
                  href={`/purchase-orders/${po.id}`}
                  className="flex items-center justify-between gap-4 rounded-lg px-2 py-3 transition-colors hover:bg-muted/50"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{po.vendor_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {po.po_number} · {po.total.toLocaleString()}
                    </p>
                  </div>
                  <Badge variant="outline" className={PO_STATUS_STYLE[po.status]}>
                    {po.status}
                  </Badge>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

const INSIGHT_ICON: Record<ProcurementInsight["category"], typeof Lightbulb> = {
  risk: ShieldQuestion,
  savings: TrendingUp,
  quality: Gauge,
  general: Lightbulb,
};

const INSIGHT_LABEL: Record<ProcurementInsight["category"], string> = {
  risk: "Risk",
  savings: "Savings",
  quality: "Quality",
  general: "General",
};

function AIInsightsPanel() {
  const [insights, setInsights] = useState<ProcurementInsight[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    procurementApi
      .getInsights()
      .then((res) => setInsights(res.items))
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load insights")
      );
  }, []);

  return (
    <Card className="border-intelligence/20">
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-intelligence" />
          AI Insights
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        {error && <p className="text-sm text-destructive">{error}</p>}
        {!error && insights === null && (
          <div className="space-y-2">
            <Skeleton className="h-9 w-full" />
            <Skeleton className="h-9 w-full" />
          </div>
        )}
        {insights !== null && insights.length === 0 && (
          <p className="py-4 text-sm text-muted-foreground">
            No insights yet. They surface automatically as RFQs, quotes, and recommendations accumulate.
          </p>
        )}
        {insights !== null && insights.length > 0 && (
          <ul className="space-y-3">
            {insights.map((insight) => {
              const Icon = INSIGHT_ICON[insight.category];
              return (
                <li key={insight.id} className="flex items-start gap-3">
                  <Icon className="mt-0.5 h-4 w-4 shrink-0 text-intelligence" />
                  <div className="min-w-0">
                    <p className="text-sm">{insight.summary}</p>
                    <Badge variant="outline" className="mt-1 text-[10px] text-muted-foreground">
                      {INSIGHT_LABEL[insight.category]}
                    </Badge>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  return (
    <>
      <Topbar title="Dashboard" />
      <main className="flex-1 space-y-8 p-6">
        <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr] lg:items-center">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="space-y-4"
          >
            <p className="font-mono text-xs font-medium tracking-[0.2em] text-intelligence uppercase">
              SupplyX
            </p>
            <h2 className="font-serif text-4xl leading-[1.05] tracking-tight sm:text-5xl">
              Your procurement decisions,
              <br />
              compressed into intelligence.
            </h2>
            <p className="max-w-xl text-sm text-muted-foreground sm:text-base">
              Turn fragmented vendor quotations into transparent, explainable
              procurement decisions.
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              <Button render={<Link href="/rfqs/new" />}>New RFQ</Button>
              <Button variant="outline" render={<Link href="/rfqs" />}>
                Analyze Quotes
              </Button>
              <Button variant="outline" render={<Link href="/rfqs" />}>
                View Recommendations
              </Button>
            </div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="space-y-2"
          >
            <p className="text-center font-mono text-[10px] font-medium tracking-[0.2em] text-muted-foreground uppercase">
              Live Procurement Pulse
            </p>
            <ProcurementIntelligenceScene className="h-72 w-full sm:h-96" />
          </motion.div>
        </div>

        <PipelineOverview />

        <MetricsGrid />

        <RecentRFQs />

        <div className="grid gap-6 lg:grid-cols-2">
          <RecentPurchaseOrders />
          <AIInsightsPanel />
        </div>
      </main>
    </>
  );
}
