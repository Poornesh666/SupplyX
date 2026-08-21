"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ClipboardList, Gauge, ShieldAlert, TrendingUp, Wallet } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Topbar } from "@/components/layout/topbar";
import { procurementApi } from "@/lib/procurement-api";
import type {
  DashboardMetrics,
  FinanceSummary,
  RFQ,
  RiskLevel,
  RiskSeverity,
  Vendor,
} from "@/types/procurement";

const RISK_STYLE: Record<RiskLevel, string> = {
  low: "border-emerald-500/40 text-emerald-600 dark:text-emerald-400",
  medium: "border-amber-500/40 text-amber-600 dark:text-amber-400",
  high: "border-destructive/40 text-destructive",
};

const SEVERITY_COLOR: Record<RiskSeverity, string> = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "var(--destructive)",
};

interface StatCardProps {
  label: string;
  value: string;
  icon: typeof ClipboardList;
  hint: string;
}

function StatCard({ label, value, icon: Icon, hint }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xs font-medium text-muted-foreground">{label}</CardTitle>
        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold tabular-nums">{value}</div>
        <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
      </CardContent>
    </Card>
  );
}

type LoadState =
  | { status: "loading" }
  | {
      status: "success";
      rfqs: RFQ[];
      vendors: Vendor[];
      metrics: DashboardMetrics;
      finance: FinanceSummary | null;
      riskCounts: Record<RiskSeverity, number>;
    }
  | { status: "error"; message: string };

export default function AnalyticsPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [rfqsRes, vendorsRes, metrics] = await Promise.all([
          procurementApi.listRFQs(),
          procurementApi.listVendors(),
          procurementApi.getDashboardMetrics(),
        ]);

        let finance: FinanceSummary | null = null;
        try {
          finance = await procurementApi.getFinanceSummary();
        } catch {
          finance = null;
        }

        const riskCounts: Record<RiskSeverity, number> = { low: 0, medium: 0, high: 0 };
        const quoteLists = await Promise.all(
          rfqsRes.items.map((rfq) =>
            procurementApi.listQuotes(rfq.id).catch(() => ({ items: [], total: 0 }))
          )
        );
        quoteLists.forEach((res) => {
          res.items.forEach((quote) => {
            quote.risks.forEach((risk) => {
              riskCounts[risk.severity] += 1;
            });
          });
        });

        if (!cancelled) {
          setState({
            status: "success",
            rfqs: rfqsRes.items,
            vendors: vendorsRes.items,
            metrics,
            finance,
            riskCounts,
          });
        }
      } catch (err) {
        if (!cancelled) {
          setState({
            status: "error",
            message: err instanceof Error ? err.message : "Failed to load analytics",
          });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.status === "loading") {
    return (
      <>
        <Topbar title="Analytics" />
        <main className="flex-1 space-y-6 p-6">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
          <Skeleton className="h-64 w-full" />
        </main>
      </>
    );
  }

  if (state.status === "error") {
    return (
      <>
        <Topbar title="Analytics" />
        <main className="p-6 text-sm text-destructive">{state.message}</main>
      </>
    );
  }

  const { rfqs, vendors, metrics, finance, riskCounts } = state;

  const averageVendorScore =
    vendors.length > 0
      ? vendors.reduce(
          (sum, v) => sum + (v.reliability_score + v.quality_score + v.payment_score) / 3,
          0
        ) / vendors.length
      : null;

  const chartData = (["high", "medium", "low"] as RiskSeverity[]).map((severity) => ({
    severity,
    label: severity[0].toUpperCase() + severity.slice(1),
    count: riskCounts[severity],
  }));
  const totalRisks = chartData.reduce((sum, d) => sum + d.count, 0);

  return (
    <>
      <Topbar title="Analytics" />
      <main className="flex-1 space-y-8 p-6">
        <div>
          <h2 className="font-serif text-3xl tracking-tight">Procurement Overview</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Real-time metrics compiled from RFQs, vendors, and recommendations.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard
            label="Total RFQs"
            value={rfqs.length.toLocaleString()}
            icon={ClipboardList}
            hint="Across the procurement pipeline"
          />
          {finance && (
            <StatCard
              label="Total Spend"
              value={finance.total_procurement_spend.toLocaleString()}
              icon={Wallet}
              hint="Committed across purchase orders"
            />
          )}
          <StatCard
            label="Potential Savings"
            value={metrics.potential_savings.toLocaleString()}
            icon={TrendingUp}
            hint="Identified by deterministic scoring"
          />
          <StatCard
            label="Average Vendor Score"
            value={averageVendorScore !== null ? averageVendorScore.toFixed(1) : "—"}
            icon={Gauge}
            hint="Reliability + quality + payment"
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Vendor Performance</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {vendors.length === 0 ? (
              <p className="p-6 text-sm text-muted-foreground">
                No vendors yet. Vendor performance appears here once vendors are added.
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Vendor</TableHead>
                    <TableHead>Reliability</TableHead>
                    <TableHead>Quality</TableHead>
                    <TableHead>Payment</TableHead>
                    <TableHead>Risk</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {vendors.map((vendor) => (
                    <TableRow key={vendor.id}>
                      <TableCell>
                        <div className="font-medium">{vendor.company}</div>
                        <div className="text-xs text-muted-foreground">{vendor.vendor_id}</div>
                      </TableCell>
                      <TableCell>{vendor.reliability_score}</TableCell>
                      <TableCell>{vendor.quality_score}</TableCell>
                      <TableCell>{vendor.payment_score}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={RISK_STYLE[vendor.risk_level]}>
                          {vendor.risk_level}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-muted-foreground" />
              Risk Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            {totalRisks === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                No risks detected yet. This chart populates as quotes are analyzed.
              </p>
            ) : (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-border" />
                    <XAxis
                      dataKey="label"
                      tickLine={false}
                      axisLine={false}
                      className="fill-muted-foreground text-xs"
                    />
                    <YAxis
                      allowDecimals={false}
                      tickLine={false}
                      axisLine={false}
                      className="fill-muted-foreground text-xs"
                    />
                    <Tooltip
                      cursor={{ fill: "var(--muted)" }}
                      contentStyle={{
                        background: "var(--popover)",
                        border: "1px solid var(--border)",
                        borderRadius: "8px",
                        fontSize: "12px",
                        color: "var(--popover-foreground)",
                      }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry) => (
                        <Cell key={entry.severity} fill={SEVERITY_COLOR[entry.severity]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </>
  );
}
