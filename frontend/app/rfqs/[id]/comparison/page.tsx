"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { SlidersHorizontal, Sparkles, Trophy } from "lucide-react";

import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RiskSeverityBadge } from "@/components/procurement/risk-badge";
import { useCountUp } from "@/components/procurement/score-bar";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { procurementApi } from "@/lib/procurement-api";
import { cn } from "@/lib/utils";
import type { ComparisonResponse } from "@/types/procurement";

const SCORE_ROWS: { key: keyof ComparisonResponse["entries"][number]["score"]; label: string }[] = [
  { key: "price", label: "Price" },
  { key: "delivery", label: "Delivery" },
  { key: "quality", label: "Quality" },
  { key: "reliability", label: "Reliability" },
  { key: "payment", label: "Payment" },
  { key: "risk", label: "Risk" },
];

function ScoreCell({
  value,
  max,
  isWinner,
}: {
  value: number;
  max: number;
  isWinner: boolean;
}) {
  const percent = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  return (
    <div className="mx-auto flex w-20 flex-col items-center gap-1">
      <span className="tabular-nums">{value}</span>
      <div className="h-1 w-full overflow-hidden rounded-full bg-muted">
        <motion.div
          className={cn("h-full rounded-full", isWinner ? "bg-emerald-500" : "bg-primary/60")}
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

function CountUpNumber({ value, className }: { value: number; className?: string }) {
  const animated = useCountUp(value);
  return <span className={cn("tabular-nums", className)}>{Math.round(animated).toLocaleString()}</span>;
}

export default function ComparisonPage() {
  const params = useParams<{ id: string }>();
  const rfqId = params.id;

  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    procurementApi
      .getComparison(rfqId)
      .then(setComparison)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load comparison"));
  }, [rfqId]);

  return (
    <>
      <Topbar title="Vendor comparison" />
      <main className="flex-1 space-y-6 p-6">
        {error && (
          <Card>
            <CardContent className="pt-6 text-sm text-muted-foreground">{error}</CardContent>
          </Card>
        )}

        {!error && !comparison && (
          <div className="space-y-4">
            <Skeleton className="h-8 w-1/3" />
            <Skeleton className="h-64 w-full" />
          </div>
        )}

        {comparison && (
          <>
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Deterministic scores computed from extracted quotes, vendor baselines, and
                detected risks. Weights: price {comparison.weights.price}, delivery{" "}
                {comparison.weights.delivery}, quality {comparison.weights.quality}, reliability{" "}
                {comparison.weights.reliability}, payment {comparison.weights.payment}, risk{" "}
                {comparison.weights.risk}.
              </p>
              <div className="flex items-center gap-2">
                <Button variant="outline" render={<Link href={`/rfqs/${rfqId}/what-if`} />}>
                  <SlidersHorizontal className="h-4 w-4" />
                  What-if simulator
                </Button>
                <Button render={<Link href={`/rfqs/${rfqId}/recommendation`} />}>
                  <Sparkles className="h-4 w-4" />
                  AI Recommendation
                </Button>
              </div>
            </div>

            {(() => {
              const winner = comparison.entries.find(
                (e) => e.vendor_id === comparison.recommended_vendor_id
              );
              const cheapest = comparison.entries.find(
                (e) => e.vendor_id === comparison.lowest_price_vendor_id
              );
              if (!winner || !cheapest || winner.vendor_id === cheapest.vendor_id) return null;
              const premium =
                ((winner.calculated_total - cheapest.calculated_total) / cheapest.calculated_total) *
                100;
              return (
                <Card className="border-intelligence/25 bg-intelligence/[0.04]">
                  <CardContent className="flex items-start gap-3 pt-6">
                    <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-intelligence" />
                    <p className="text-sm leading-relaxed">
                      <span className="font-medium">{winner.vendor_name}</span> wins despite
                      costing {premium.toFixed(1)}% more than the cheapest quote from{" "}
                      <span className="font-medium">{cheapest.vendor_name}</span> — the price
                      difference is outweighed by stronger delivery, quality, reliability, and
                      risk scores. Lowest price is not automatically the best decision.
                    </p>
                  </CardContent>
                </Card>
              );
            })()}

            <Card>
              <CardHeader>
                <CardTitle>Score breakdown</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Criteria</TableHead>
                      {comparison.entries.map((entry) => {
                        const isWinner = entry.vendor_id === comparison.recommended_vendor_id;
                        return (
                          <TableHead
                            key={entry.vendor_id}
                            className={cn(
                              "text-center transition-colors",
                              isWinner && "bg-emerald-500/5"
                            )}
                          >
                            <div className="flex items-center justify-center gap-1">
                              {entry.vendor_name}
                              {isWinner && (
                                <motion.span
                                  initial={{ scale: 0, rotate: -20 }}
                                  animate={{ scale: 1, rotate: 0 }}
                                  transition={{ duration: 0.3, delay: 0.2, ease: "easeOut" }}
                                >
                                  <Trophy className="h-3.5 w-3.5 text-amber-500" />
                                </motion.span>
                              )}
                            </div>
                          </TableHead>
                        );
                      })}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {SCORE_ROWS.map((row, rowIndex) => (
                      <motion.tr
                        key={row.key}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.3, delay: rowIndex * 0.05 }}
                        className="border-b"
                      >
                        <TableCell className="text-muted-foreground">{row.label}</TableCell>
                        {comparison.entries.map((entry) => (
                          <TableCell
                            key={entry.vendor_id}
                            className={cn(
                              entry.vendor_id === comparison.recommended_vendor_id &&
                                "bg-emerald-500/5"
                            )}
                          >
                            <ScoreCell
                              value={entry.score[row.key]}
                              max={comparison.weights[row.key]}
                              isWinner={entry.vendor_id === comparison.recommended_vendor_id}
                            />
                          </TableCell>
                        ))}
                      </motion.tr>
                    ))}
                    <TableRow className="font-semibold">
                      <TableCell>TOTAL</TableCell>
                      {comparison.entries.map((entry) => (
                        <TableCell
                          key={entry.vendor_id}
                          className={cn(
                            "text-center text-base",
                            entry.vendor_id === comparison.recommended_vendor_id &&
                              "bg-emerald-500/5 text-emerald-600 dark:text-emerald-400"
                          )}
                        >
                          <CountUpNumber value={entry.total_score} />
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="text-muted-foreground">Rank</TableCell>
                      {comparison.entries.map((entry) => (
                        <TableCell key={entry.vendor_id} className="text-center">
                          <motion.span
                            className="inline-flex"
                            initial={{ opacity: 0, scale: 0.85 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ duration: 0.25, delay: 0.1 * entry.rank, ease: "easeOut" }}
                          >
                            <Badge
                              variant="outline"
                              className={
                                entry.rank === 1
                                  ? "border-emerald-500/40 text-emerald-600 dark:text-emerald-400"
                                  : ""
                              }
                            >
                              #{entry.rank}
                            </Badge>
                          </motion.span>
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="text-muted-foreground">Calculated total</TableCell>
                      {comparison.entries.map((entry) => (
                        <TableCell key={entry.vendor_id} className="text-center">
                          <CountUpNumber value={entry.calculated_total} />
                          {entry.vendor_id === comparison.lowest_price_vendor_id && (
                            <span className="ml-1 text-xs text-muted-foreground">
                              (lowest)
                            </span>
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {comparison.entries.map((entry, index) => {
                const isWinner = entry.vendor_id === comparison.recommended_vendor_id;
                return (
                  <motion.div
                    key={entry.vendor_id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.06, ease: "easeOut" }}
                  >
                    <Card
                      className={cn(
                        "h-full transition-shadow duration-200 hover:shadow-md",
                        isWinner && "ring-2 ring-emerald-500/30"
                      )}
                    >
                      <CardHeader>
                        <CardTitle className="flex items-center justify-between text-base">
                          <span className="flex items-center gap-1.5">
                            {entry.vendor_name}
                            {isWinner && <Trophy className="h-3.5 w-3.5 text-amber-500" />}
                          </span>
                          <Badge
                            variant="outline"
                            className={isWinner ? "border-emerald-500/40 text-emerald-600 dark:text-emerald-400" : ""}
                          >
                            #{entry.rank}
                          </Badge>
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        {entry.risks.length === 0 ? (
                          <p className="text-sm text-muted-foreground">No risks detected.</p>
                        ) : (
                          entry.risks.map((risk, i) => (
                            <div key={i} className="flex items-start gap-2 text-sm">
                              <RiskSeverityBadge severity={risk.severity} />
                              <span>{risk.description}</span>
                            </div>
                          ))
                        )}
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </div>
          </>
        )}
      </main>
    </>
  );
}
