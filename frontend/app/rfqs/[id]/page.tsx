"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, ChevronDown, FileText, Package, ShoppingCart, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Topbar } from "@/components/layout/topbar";
import { AuditTimeline } from "@/components/procurement/audit-timeline";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { QuoteCard } from "@/components/procurement/quote-card";
import { QuoteUploadForm } from "@/components/procurement/quote-upload-form";
import { RFQStatusBadge } from "@/components/procurement/status-badge";
import { WorkflowTimeline } from "@/components/procurement/workflow-timeline";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api";
import { procurementApi } from "@/lib/procurement-api";
import type { PurchaseOrder, Quote, RFQ, Vendor } from "@/types/procurement";

export default function RFQDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const rfqId = params.id;

  const [rfq, setRfq] = useState<RFQ | null>(null);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [existingPO, setExistingPO] = useState<PurchaseOrder | null>(null);
  const [creatingPO, setCreatingPO] = useState(false);
  const [activityOpen, setActivityOpen] = useState(false);

  const load = useCallback(() => {
    Promise.all([
      procurementApi.getRFQ(rfqId),
      procurementApi.listVendors(),
      procurementApi.listQuotes(rfqId),
    ])
      .then(([rfqRes, vendorsRes, quotesRes]) => {
        setRfq(rfqRes);
        setVendors(vendorsRes.items);
        setQuotes(quotesRes.items);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load RFQ"));
  }, [rfqId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (rfq?.status !== "po_created" && rfq?.status !== "po_issued") return;
    procurementApi
      .listPurchaseOrders()
      .then((res) => setExistingPO(res.items.find((po) => po.rfq_id === rfqId) ?? null))
      .catch(() => setExistingPO(null));
  }, [rfq?.status, rfqId]);

  const handleCreatePO = async () => {
    setCreatingPO(true);
    try {
      const po = await procurementApi.createPurchaseOrder(rfqId);
      toast.success(`Purchase order ${po.po_number} created`);
      router.push(`/purchase-orders/${po.id}`);
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : err instanceof Error ? err.message : "Failed to create purchase order";
      toast.error(message);
    } finally {
      setCreatingPO(false);
    }
  };

  const invitedVendors = vendors.filter((v) => rfq?.invited_vendor_ids.includes(v.id));
  const extractedCount = quotes.filter((q) => q.status === "extracted").length;

  if (error) {
    return (
      <>
        <Topbar title="RFQ" />
        <main className="p-6 text-sm text-destructive">{error}</main>
      </>
    );
  }

  if (!rfq) {
    return (
      <>
        <Topbar title="RFQ" />
        <main className="space-y-4 p-6">
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-32 w-full" />
        </main>
      </>
    );
  }

  return (
    <>
      <Topbar title={rfq.rfq_number} />
      <main className="flex-1 space-y-6 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">{rfq.title}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{rfq.description}</p>
          </div>
          <div className="flex items-center gap-2">
            <RFQStatusBadge status={rfq.status} />
            {extractedCount >= 1 && (
              <>
                <Button variant="outline" render={<Link href={`/rfqs/${rfq.id}/comparison`} />}>
                  Compare vendors
                  <ArrowRight className="h-4 w-4" />
                </Button>
                <Button render={<Link href={`/rfqs/${rfq.id}/recommendation`} />}>
                  <Sparkles className="h-4 w-4" />
                  AI Recommendation
                </Button>
              </>
            )}
          </div>
        </div>

        <Card>
          <CardContent className="pt-6">
            <WorkflowTimeline status={rfq.status} />
          </CardContent>
        </Card>

        {rfq.status === "recommendation_ready" && (
          <Card className="border-primary/30 bg-primary/5">
            <CardContent className="flex flex-wrap items-center justify-between gap-4 pt-6">
              <div className="flex items-center gap-3">
                <Sparkles className="h-5 w-5 text-primary" />
                <div>
                  <p className="font-medium">AI recommendation is ready</p>
                  <p className="text-sm text-muted-foreground">
                    Review the recommended vendor and approve or reject to proceed.
                  </p>
                </div>
              </div>
              <Button render={<Link href={`/rfqs/${rfq.id}/recommendation`} />}>
                Review recommendation
                <ArrowRight className="h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        )}

        {rfq.status === "approved" && (
          <Card className="border-emerald-500/30 bg-emerald-500/5">
            <CardContent className="flex flex-wrap items-center justify-between gap-4 pt-6">
              <div className="flex items-center gap-3">
                <ShoppingCart className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                <div>
                  <p className="font-medium">Recommendation approved</p>
                  <p className="text-sm text-muted-foreground">
                    Create a purchase order to move this RFQ into fulfillment.
                  </p>
                </div>
              </div>
              <Button onClick={handleCreatePO} disabled={creatingPO}>
                <Package className="h-4 w-4" />
                {creatingPO ? "Creating PO..." : "Create Purchase Order"}
              </Button>
            </CardContent>
          </Card>
        )}

        {(rfq.status === "po_created" || rfq.status === "po_issued") && (
          <Card className="border-emerald-600/30 bg-emerald-600/5">
            <CardContent className="flex flex-wrap items-center justify-between gap-4 pt-6">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-emerald-700 dark:text-emerald-300" />
                <div>
                  <p className="font-medium">
                    {rfq.status === "po_issued" ? "Purchase order issued" : "Purchase order created"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {existingPO
                      ? `PO ${existingPO.po_number}`
                      : "View the purchase order for this RFQ."}
                  </p>
                </div>
              </div>
              {existingPO && (
                <Button variant="outline" render={<Link href={`/purchase-orders/${existingPO.id}`} />}>
                  View purchase order
                  <ArrowRight className="h-4 w-4" />
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        <Card>
          <CardContent className="grid grid-cols-2 gap-x-6 gap-y-4 pt-6 sm:grid-cols-4">
            <div>
              <p className="text-xs text-muted-foreground">Quantity</p>
              <p className="font-medium">
                {rfq.quantity} {rfq.unit}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Required delivery</p>
              <p className="font-medium">{rfq.required_delivery_date}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Specifications</p>
              <p className="font-medium">{rfq.specifications || "—"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Invited vendors</p>
              <div className="flex flex-wrap gap-1">
                {invitedVendors.map((v) => (
                  <Badge key={v.id} variant="outline">
                    {v.company}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Vendor quotes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <QuoteUploadForm
              rfqId={rfq.id}
              vendors={invitedVendors}
              onUploaded={(quote) =>
                setQuotes((prev) => [quote, ...prev.filter((q) => q.id !== quote.id)])
              }
            />

            {quotes.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No quotes uploaded yet. Upload a vendor quote to begin AI extraction.
              </p>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {quotes.map((quote) => (
                  <QuoteCard
                    key={quote.id}
                    quote={quote}
                    vendor={vendors.find((v) => v.id === quote.vendor_id)}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            className="flex flex-row cursor-pointer items-center justify-between space-y-0"
            onClick={() => setActivityOpen((open) => !open)}
          >
            <CardTitle>Activity</CardTitle>
            <ChevronDown
              className={`h-4 w-4 text-muted-foreground transition-transform ${activityOpen ? "rotate-180" : ""}`}
            />
          </CardHeader>
          {activityOpen && (
            <CardContent>
              <AuditTimeline rfqId={rfq.id} />
            </CardContent>
          )}
        </Card>
      </main>
    </>
  );
}
