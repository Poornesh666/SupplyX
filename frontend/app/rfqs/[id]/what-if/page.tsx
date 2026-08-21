"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Minus, TrendingDown, TrendingUp } from "lucide-react";

import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import type { ComparisonResponse, ScoreBreakdown, ScoringWeights } from "@/types/procurement";

const WEIGHT_FIELDS: { key: keyof ScoringWeights; label: string }[] = [
  { key: "price", label: "Price" },
  { key: "delivery", label: "Delivery" },
  { key: "quality", label: "Quality" },
  { key: "reliability", label: "Reliability" },
  { key: "payment", label: "Payment terms" },
  { key: "risk", label: "Risk" },
];

const DEFAULT_WEIGHTS: ScoringWeights = {
  price: 30,
  delivery: 20,
  quality: 15,
  reliability: 15,
  payment: 10,
  risk: 10,
};

const WEIGHT_SUM_EPSILON = 0.01;

type BaselineState =
  | { status: "loading" }
  | { status: "success"; data: ComparisonResponse }
  | { status: "empty" }
  | { status: "error"; message: string };

type SimulationState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: ComparisonResponse }
  | { status: "error"; message: string };

function sumWeights(weights: ScoringWeights): number {
  return WEIGHT_FIELDS.reduce((total, field) => total + (weights[field.key] || 0), 0);
}

function rankChangeIcon(delta: number) {
  if (delta > 0) return <TrendingUp className="h-3.5 w-3.5 text-emerald-500" />;
  if (delta < 0) return <TrendingDown className="h-3.5 w-3.5 text-red-500" />;
  return <Minus className="h-3.5 w-3.5 text-muted-foreground" />;
}

function explainMove(
  vendorName: string,
  baselineEntry: ComparisonResponse["entries"][number],
  simulatedEntry: ComparisonResponse["entries"][number]
): string | null {
  const rankDelta = baselineEntry.rank - simulatedEntry.rank;
  if (rankDelta === 0) return null;

  let biggestKey: keyof ScoreBreakdown | null = null;
  let biggestDelta = 0;
  (Object.keys(simulatedEntry.score) as (keyof ScoreBreakdown)[]).forEach((key) => {
    const delta = simulatedEntry.score[key] - baselineEntry.score[key];
    if (Math.abs(delta) > Math.abs(biggestDelta)) {
      biggestDelta = delta;
      biggestKey = key;
    }
  });

  if (!biggestKey || Math.abs(biggestDelta) < 0.05) return null;

  const direction = rankDelta > 0 ? "moves up" : "moves down";
  const field = WEIGHT_FIELDS.find((f) => f.key === biggestKey)?.label ?? biggestKey;
  const changeWord = biggestDelta > 0 ? "increased" : "decreased";
  return `${vendorName} ${direction} because its ${field.toLowerCase()} score ${changeWord} by ${Math.abs(
    biggestDelta
  ).toFixed(1)} pts under the new weights.`;
}

export default function WhatIfPage() {
  const params = useParams<{ id: string }>();
  const rfqId = params.id;

  const [baseline, setBaseline] = useState<BaselineState>({ status: "loading" });
  const [weights, setWeights] = useState<ScoringWeights>(DEFAULT_WEIGHTS);
  const [simulation, setSimulation] = useState<SimulationState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;

    procurementApi
      .getComparison(rfqId)
      .then((data) => {
        if (cancelled) return;
        if (data.entries.length === 0) {
          setBaseline({ status: "empty" });
        } else {
          setBaseline({ status: "success", data });
        }
      })
      .catch((err) => {
        if (cancelled) return;
        setBaseline({
          status: "error",
          message: err instanceof Error ? err.message : "Failed to load comparison",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [rfqId]);

  const sum = useMemo(() => sumWeights(weights), [weights]);
  const isBalanced = Math.abs(sum - 100) <= WEIGHT_SUM_EPSILON;

  function handleWeightChange(key: keyof ScoringWeights, rawValue: string) {
    const value = Number(rawValue);
    setWeights((prev) => ({ ...prev, [key]: Number.isFinite(value) ? value : 0 }));
  }

  function handleReset() {
    setWeights(DEFAULT_WEIGHTS);
    setSimulation({ status: "idle" });
  }

  async function handleSimulate() {
    if (!isBalanced) return;
    setSimulation({ status: "loading" });
    try {
      const data = await procurementApi.simulateWhatIf(rfqId, weights);
      setSimulation({ status: "success", data });
    } catch (err) {
      setSimulation({
        status: "error",
        message: err instanceof Error ? err.message : "Simulation failed",
      });
    }
  }

  const baselineByVendor = useMemo(() => {
    if (baseline.status !== "success") return new Map<string, ComparisonResponse["entries"][number]>();
    return new Map(baseline.data.entries.map((e) => [e.vendor_id, e]));
  }, [baseline]);

  const explanations =
    simulation.status === "success" && baseline.status === "success"
      ? simulation.data.entries
          .map((entry) => {
            const base = baselineByVendor.get(entry.vendor_id);
            if (!base) return null;
            return explainMove(entry.vendor_name, base, entry);
          })
          .filter((line): line is string => Boolean(line))
      : [];

  return (
    <>
      <Topbar title="What-if simulator" />
      <main className="flex-1 space-y-6 p-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Adjust scoring weights to see how the vendor ranking would change — nothing here is
            saved.
          </p>
          <Button variant="outline" render={<Link href={`/rfqs/${rfqId}/comparison`} />}>
            <ArrowLeft className="h-4 w-4" />
            Back to comparison
          </Button>
        </div>

        {baseline.status === "loading" && (
          <div className="space-y-4">
            <Skeleton className="h-8 w-1/3" />
            <Skeleton className="h-64 w-full" />
          </div>
        )}

        {baseline.status === "error" && (
          <Card>
            <CardContent className="pt-6 text-sm text-muted-foreground">
              {baseline.message}
            </CardContent>
          </Card>
        )}

        {baseline.status === "empty" && (
          <Card>
            <CardContent className="pt-6 text-sm text-muted-foreground">
              No extracted quotes yet for this RFQ — upload and analyze vendor quotes before
              running a simulation.
            </CardContent>
          </Card>
        )}

        {baseline.status === "success" && (
          <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
            <Card className="h-fit">
              <CardHeader>
                <CardTitle className="text-base">Scoring weights</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {WEIGHT_FIELDS.map((field) => (
                  <div key={field.key} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <Label htmlFor={`weight-${field.key}`}>{field.label}</Label>
                      <Input
                        id={`weight-${field.key}`}
                        type="number"
                        min={0}
                        max={100}
                        step={1}
                        value={weights[field.key]}
                        onChange={(e) => handleWeightChange(field.key, e.target.value)}
                        className="w-16 text-right"
                      />
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      step={1}
                      value={weights[field.key]}
                      onChange={(e) => handleWeightChange(field.key, e.target.value)}
                      className="w-full accent-primary"
                      aria-label={`${field.label} weight slider`}
                    />
                  </div>
                ))}

                <div className="flex items-center justify-between border-t border-border pt-3 text-sm">
                  <span className="text-muted-foreground">Total</span>
                  <span
                    className={cn(
                      "font-semibold tabular-nums",
                      isBalanced ? "text-emerald-600 dark:text-emerald-400" : "text-red-500"
                    )}
                  >
                    {sum}%
                  </span>
                </div>
                {!isBalanced && (
                  <p className="text-xs text-red-500">
                    Weights must sum to exactly 100 before you can simulate.
                  </p>
                )}

                <div className="flex gap-2 pt-1">
                  <Button
                    className="flex-1"
                    disabled={!isBalanced || simulation.status === "loading"}
                    onClick={handleSimulate}
                  >
                    {simulation.status === "loading" ? "Simulating..." : "Simulate"}
                  </Button>
                  <Button variant="outline" onClick={handleReset}>
                    Reset
                  </Button>
                </div>

                {simulation.status === "error" && (
                  <p className="text-xs text-red-500">{simulation.message}</p>
                )}
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    {simulation.status === "success" ? "Current vs. simulated ranking" : "Current ranking"}
                  </CardTitle>
                </CardHeader>
                <CardContent className="overflow-x-auto p-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Vendor</TableHead>
                        <TableHead className="text-center">Current rank</TableHead>
                        <TableHead className="text-center">Current score</TableHead>
                        {simulation.status === "success" && (
                          <>
                            <TableHead className="text-center">Simulated rank</TableHead>
                            <TableHead className="text-center">Simulated score</TableHead>
                            <TableHead className="text-center">Change</TableHead>
                          </>
                        )}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {baseline.data.entries.map((entry) => {
                        const simEntry =
                          simulation.status === "success"
                            ? simulation.data.entries.find((e) => e.vendor_id === entry.vendor_id)
                            : undefined;
                        const rankDelta = simEntry ? entry.rank - simEntry.rank : 0;

                        return (
                          <TableRow key={entry.vendor_id}>
                            <TableCell className="font-medium">{entry.vendor_name}</TableCell>
                            <TableCell className="text-center">
                              <Badge variant="outline">#{entry.rank}</Badge>
                            </TableCell>
                            <TableCell className="text-center tabular-nums">
                              {entry.total_score}
                            </TableCell>
                            {simulation.status === "success" && simEntry && (
                              <>
                                <TableCell className="text-center">
                                  <Badge
                                    variant="outline"
                                    className={
                                      simEntry.rank === 1
                                        ? "border-emerald-500/40 text-emerald-600 dark:text-emerald-400"
                                        : ""
                                    }
                                  >
                                    #{simEntry.rank}
                                  </Badge>
                                </TableCell>
                                <TableCell className="text-center tabular-nums">
                                  {simEntry.total_score}
                                </TableCell>
                                <TableCell className="text-center">
                                  <div className="flex items-center justify-center gap-1.5">
                                    {rankChangeIcon(rankDelta)}
                                    <span
                                      className={cn(
                                        "text-xs font-medium tabular-nums",
                                        rankDelta > 0 && "text-emerald-600 dark:text-emerald-400",
                                        rankDelta < 0 && "text-red-500"
                                      )}
                                    >
                                      {rankDelta === 0
                                        ? "no change"
                                        : `#${entry.rank} → #${simEntry.rank}`}
                                    </span>
                                  </div>
                                </TableCell>
                              </>
                            )}
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              {explanations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Why the ranking changed</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {explanations.map((line, i) => (
                      <p key={i} className="text-sm text-muted-foreground">
                        {line}
                      </p>
                    ))}
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}
      </main>
    </>
  );
}
