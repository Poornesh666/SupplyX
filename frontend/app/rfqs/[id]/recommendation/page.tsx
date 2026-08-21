"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  BarChart3,
  CalendarClock,
  CheckCircle2,
  Cpu,
  Scale,
  ShieldAlert,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  TrendingDown,
  Trophy,
} from "lucide-react";

import { Topbar } from "@/components/layout/topbar";
import { ApprovalDialog } from "@/components/procurement/approval-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TotalScoreRing } from "@/components/procurement/score-bar";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api";
import { procurementApi } from "@/lib/procurement-api";
import type { ApprovalResponse, Confidence, RecommendationResponse, RFQ } from "@/types/procurement";

const CONFIDENCE_STYLE: Record<Confidence, string> = {
  high: "border-emerald-500/40 text-emerald-600 dark:text-emerald-400",
  medium: "border-amber-500/40 text-amber-600 dark:text-amber-400",
  low: "border-destructive/40 text-destructive",
};

export default function RecommendationPage() {
  const params = useParams<{ id: string }>();
  const rfqId = params.id;

  const [rfq, setRfq] = useState<RFQ | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [approval, setApproval] = useState<ApprovalResponse | null>(null);
  const [approvalLoaded, setApprovalLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const load = useCallback(() => {
    Promise.all([
      procurementApi.getRFQ(rfqId),
      procurementApi.getRecommendation(rfqId),
      procurementApi.getApproval(rfqId).catch((err) => {
        if (err instanceof ApiError && err.status === 404) return null;
        throw err;
      }),
    ])
      .then(([rfqRes, recRes, approvalRes]) => {
        setRfq(rfqRes);
        setRecommendation(recRes);
        setApproval(approvalRes);
        setApprovalLoaded(true);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to generate recommendation")
      );
  }, [rfqId]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) {
    return (
      <>
        <Topbar title="AI Recommendation" />
        <main className="p-6">
          <Card>
            <CardContent className="pt-6 text-sm text-muted-foreground">{error}</CardContent>
          </Card>
        </main>
      </>
    );
  }

  if (!recommendation || !rfq || !approvalLoaded) {
    return (
      <>
        <Topbar title="AI Recommendation" />
        <main className="space-y-4 p-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4 animate-pulse" />
            Generating AI recommendation from deterministic scores...
          </div>
          <Skeleton className="h-64 w-full" />
        </main>
      </>
    );
  }

  const { explanation } = recommendation;
  const canDecide = rfq.status === "recommendation_ready" && !approval;

  return (
    <>
      <Topbar title="AI Recommendation" />
      <main className="flex-1 space-y-6 p-6">
        {/* Hero: AI procurement verdict */}
        <Card className="overflow-hidden border-intelligence/25 bg-gradient-to-br from-intelligence/[0.04] to-transparent">
          <CardContent className="flex flex-col items-center gap-6 pt-6 text-center sm:flex-row sm:text-left">
            <TotalScoreRing score={recommendation.recommended_score} />
            <div className="flex-1">
              <p className="flex items-center justify-center gap-1.5 font-mono text-xs font-medium tracking-[0.15em] text-intelligence uppercase sm:justify-start">
                <Trophy className="h-3.5 w-3.5" />
                AI Procurement Verdict
              </p>
              <h2 className="mt-1 font-serif text-4xl tracking-tight sm:text-5xl">
                {recommendation.recommended_vendor_name}
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Score {recommendation.recommended_score}/100
              </p>
              <div className="mt-3 flex flex-wrap items-center justify-center gap-2 sm:justify-start">
                <Badge variant="outline" className={CONFIDENCE_STYLE[explanation.confidence]}>
                  {explanation.confidence} confidence
                </Badge>
                {recommendation.potential_savings != null && (
                  <Badge
                    variant="outline"
                    className="gap-1 border-emerald-500/40 text-emerald-600 dark:text-emerald-400"
                  >
                    <TrendingDown className="h-3 w-3" />
                    Potential savings: {recommendation.potential_savings.toLocaleString()}
                  </Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Approval action / outcome */}
        {canDecide && (
          <Card className="border-primary/30 bg-primary/5">
            <CardContent className="flex flex-wrap items-center justify-between gap-4 pt-6">
              <div>
                <p className="font-medium">Decision required</p>
                <p className="text-sm text-muted-foreground">
                  Approve to proceed to purchase order, or reject with a reason.
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="destructive" onClick={() => setDialogOpen(true)}>
                  <ThumbsDown className="h-4 w-4" />
                  Reject
                </Button>
                <Button onClick={() => setDialogOpen(true)}>
                  <ThumbsUp className="h-4 w-4" />
                  Approve
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {approval && (
          <Card
            className={
              approval.decision === "approved"
                ? "border-emerald-500/30 bg-emerald-500/5"
                : "border-destructive/30 bg-destructive/5"
            }
          >
            <CardContent className="space-y-2 pt-6">
              <div className="flex items-center gap-2">
                {approval.decision === "approved" ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                ) : (
                  <ShieldAlert className="h-5 w-5 text-destructive" />
                )}
                <p className="font-medium">
                  {approval.decision === "approved" ? "Approved" : "Rejected"} by{" "}
                  {approval.approver_name}
                </p>
              </div>
              <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <CalendarClock className="h-3.5 w-3.5" />
                {new Date(approval.decided_at).toLocaleString()}
              </p>
              {approval.note && (
                <p className="rounded-md bg-background/60 px-3 py-2 text-sm">{approval.note}</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* CALCULATED BY SUPPLYX DECISION ENGINE */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-foreground" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">
              Calculated by SupplyX Decision Engine
            </h3>
          </div>
          <p className="text-xs text-muted-foreground">
            Deterministic application logic — score, rank, and totals. No AI model can alter
            these numbers.
          </p>
          <Card>
            <CardContent className="grid gap-4 pt-6 sm:grid-cols-3">
              <div>
                <p className="text-xs text-muted-foreground">Recommended score</p>
                <p className="text-lg font-semibold tabular-nums">
                  {recommendation.recommended_score}/100
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Alternative vendor</p>
                {recommendation.alternative_vendor_name ? (
                  <p className="text-lg font-semibold tabular-nums">
                    {recommendation.alternative_vendor_name} — {recommendation.alternative_score}/100
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground">None scored</p>
                )}
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Potential savings</p>
                <p className="text-lg font-semibold tabular-nums">
                  {recommendation.potential_savings != null
                    ? recommendation.potential_savings.toLocaleString()
                    : "—"}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* AI-GENERATED EXPLANATION */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-primary">
              AI-Generated Explanation
            </h3>
          </div>
          <p className="text-xs text-muted-foreground">
            Written reasoning generated by AI to help you interpret the score above. It cannot
            change the score or the ranking.
          </p>

          <Card className="border-primary/15">
            <CardContent className="pt-6">
              <p className="text-sm leading-relaxed">{explanation.recommendation_summary}</p>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  Why this vendor?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm">
                  {explanation.why_recommended.map((reason, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                      {reason}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  Key strengths
                </CardTitle>
              </CardHeader>
              <CardContent>
                {explanation.key_strengths.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No notable strengths listed.</p>
                ) : (
                  <ul className="space-y-2 text-sm">
                    {explanation.key_strengths.map((strength, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                        {strength}
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Scale className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                  Trade-offs
                </CardTitle>
              </CardHeader>
              <CardContent>
                {explanation.tradeoffs.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No significant trade-offs.</p>
                ) : (
                  <ul className="space-y-2 text-sm">
                    {explanation.tradeoffs.map((tradeoff, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="mt-0.5">⚠</span>
                        {tradeoff}
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <ShieldAlert className="h-4 w-4 text-destructive" />
                  Key risks
                </CardTitle>
              </CardHeader>
              <CardContent>
                {explanation.key_risks.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No significant risks.</p>
                ) : (
                  <ul className="space-y-2 text-sm">
                    {explanation.key_risks.map((risk, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-destructive" />
                        {risk}
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Full explanation</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {explanation.explanation}
              </p>
            </CardContent>
          </Card>
        </div>

        <Button variant="outline" render={<Link href={`/rfqs/${rfqId}/comparison`} />}>
          <BarChart3 className="h-4 w-4" />
          View score breakdown
        </Button>
      </main>

      <ApprovalDialog
        rfqId={rfqId}
        vendorName={recommendation.recommended_vendor_name}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onDecided={(newApproval) => {
          setApproval(newApproval);
          // Refresh RFQ so status reflects the decision (approved/rejected).
          procurementApi.getRFQ(rfqId).then(setRfq).catch(() => {});
        }}
      />
    </>
  );
}
