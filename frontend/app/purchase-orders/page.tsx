"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Topbar } from "@/components/layout/topbar";
import { Card, CardContent } from "@/components/ui/card";
import { PurchaseOrderStatusBadge } from "@/components/procurement/po-document";
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
import type { PurchaseOrder } from "@/types/procurement";

export default function PurchaseOrdersPage() {
  const [orders, setOrders] = useState<PurchaseOrder[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    procurementApi
      .listPurchaseOrders()
      .then((res) => setOrders(res.items))
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load purchase orders")
      );
  }, []);

  return (
    <>
      <Topbar title="Purchase Orders" />
      <main className="flex-1 space-y-6 p-6">
        <p className="text-sm text-muted-foreground">
          Purchase orders generated from approved procurement recommendations.
        </p>

        <Card>
          <CardContent className="p-0">
            {error && <p className="p-6 text-sm text-destructive">{error}</p>}
            {!error && orders === null && (
              <div className="space-y-2 p-6">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            )}
            {orders !== null && orders.length === 0 && (
              <p className="p-6 text-sm text-muted-foreground">
                No purchase orders yet. Approve an RFQ recommendation to create one.
              </p>
            )}
            {orders !== null && orders.length > 0 && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>PO Number</TableHead>
                    <TableHead>RFQ</TableHead>
                    <TableHead>Vendor</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orders.map((po) => (
                    <TableRow key={po.id} className="cursor-pointer">
                      <TableCell>
                        <Link
                          href={`/purchase-orders/${po.id}`}
                          className="font-medium underline-offset-2 hover:underline"
                        >
                          {po.po_number}
                        </Link>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{po.rfq_number}</TableCell>
                      <TableCell>{po.vendor_name}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        {po.total.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </TableCell>
                      <TableCell>
                        <PurchaseOrderStatusBadge status={po.status} />
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(po.created_at).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </main>
    </>
  );
}
