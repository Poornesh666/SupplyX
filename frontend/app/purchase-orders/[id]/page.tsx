"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Ban, CheckCircle2, PackageCheck, Printer, Send } from "lucide-react";
import { toast } from "sonner";

import { Topbar } from "@/components/layout/topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PODocument } from "@/components/procurement/po-document";
import { Skeleton } from "@/components/ui/skeleton";
import { procurementApi } from "@/lib/procurement-api";
import type { PurchaseOrder, PurchaseOrderStatus } from "@/types/procurement";

const CANCELLABLE_STATUSES: PurchaseOrderStatus[] = ["draft", "issued", "acknowledged"];

export default function PurchaseOrderDetailPage() {
  const params = useParams<{ id: string }>();
  const poId = params.id;

  const [po, setPo] = useState<PurchaseOrder | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);

  const load = useCallback(() => {
    procurementApi
      .getPurchaseOrder(poId)
      .then(setPo)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load purchase order")
      );
  }, [poId]);

  useEffect(() => {
    load();
  }, [load]);

  const updateStatus = async (status: PurchaseOrderStatus) => {
    setUpdating(true);
    try {
      const updated = await procurementApi.updatePurchaseOrderStatus(poId, status);
      setPo(updated);
      toast.success(`Purchase order marked as ${status}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update purchase order");
    } finally {
      setUpdating(false);
    }
  };

  if (error) {
    return (
      <>
        <Topbar title="Purchase Order" />
        <main className="p-6">
          <Card>
            <CardContent className="pt-6 text-sm text-destructive">{error}</CardContent>
          </Card>
        </main>
      </>
    );
  }

  if (!po) {
    return (
      <>
        <Topbar title="Purchase Order" />
        <main className="space-y-4 p-6">
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-96 w-full" />
        </main>
      </>
    );
  }

  const canCancel = CANCELLABLE_STATUSES.includes(po.status);

  return (
    <>
      <style>{`
        @media print {
          aside, header { display: none !important; }
          main { padding: 0 !important; }
        }
      `}</style>
      <div className="print:hidden">
        <Topbar title={po.po_number} />
      </div>
      <main className="flex-1 space-y-6 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
          <p className="text-sm text-muted-foreground">
            Manage the lifecycle of this purchase order.
          </p>
          <div className="flex flex-wrap gap-2">
            {po.status === "draft" && (
              <Button onClick={() => updateStatus("issued")} disabled={updating}>
                <Send className="h-4 w-4" />
                Issue PO
              </Button>
            )}
            {po.status === "issued" && (
              <Button onClick={() => updateStatus("acknowledged")} disabled={updating}>
                <CheckCircle2 className="h-4 w-4" />
                Mark Acknowledged
              </Button>
            )}
            {po.status === "acknowledged" && (
              <Button onClick={() => updateStatus("received")} disabled={updating}>
                <PackageCheck className="h-4 w-4" />
                Mark Received
              </Button>
            )}
            {canCancel && (
              <Button
                variant="destructive"
                onClick={() => updateStatus("cancelled")}
                disabled={updating}
              >
                <Ban className="h-4 w-4" />
                Cancel
              </Button>
            )}
            <Button variant="outline" onClick={() => window.print()}>
              <Printer className="h-4 w-4" />
              Print
            </Button>
          </div>
        </div>

        <PODocument po={po} />
      </main>
    </>
  );
}
