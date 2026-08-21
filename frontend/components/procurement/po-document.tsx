import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { PurchaseOrder, PurchaseOrderStatus } from "@/types/procurement";

const PO_STATUS_LABEL: Record<PurchaseOrderStatus, string> = {
  draft: "Draft",
  issued: "Issued",
  acknowledged: "Acknowledged",
  received: "Received",
  cancelled: "Cancelled",
};

const PO_STATUS_STYLE: Record<PurchaseOrderStatus, string> = {
  draft: "border-muted-foreground/30 text-muted-foreground",
  issued: "border-sky-500/40 text-sky-600 dark:text-sky-400",
  acknowledged: "border-amber-500/40 text-amber-600 dark:text-amber-400",
  received: "border-emerald-500/40 text-emerald-600 dark:text-emerald-400",
  cancelled: "border-destructive/40 text-destructive",
};

export function PurchaseOrderStatusBadge({ status }: { status: PurchaseOrderStatus }) {
  return (
    <Badge variant="outline" className={cn("text-sm", PO_STATUS_STYLE[status])}>
      {PO_STATUS_LABEL[status]}
    </Badge>
  );
}

function money(value: number) {
  return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function PODocument({ po }: { po: PurchaseOrder }) {
  return (
    <Card className="print:ring-0 print:shadow-none">
      <CardHeader className="border-b [.border-b]:pb-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Purchase Order
            </p>
            <CardTitle className="text-2xl">{po.po_number}</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              RFQ reference:{" "}
              <Link href={`/rfqs/${po.rfq_id}`} className="underline underline-offset-2 hover:text-foreground print:no-underline">
                {po.rfq_number}
              </Link>
            </p>
          </div>
          <div className="text-right">
            <PurchaseOrderStatusBadge status={po.status} />
            <p className="mt-2 text-xs text-muted-foreground">
              Created {new Date(po.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6 pt-6">
        <div className="grid gap-6 sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Vendor
            </p>
            <p className="mt-1 font-medium">{po.vendor_name}</p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Expected delivery
            </p>
            <p className="mt-1 font-medium">
              {po.expected_delivery_date
                ? new Date(po.expected_delivery_date).toLocaleDateString()
                : "Not specified"}
            </p>
          </div>
        </div>

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Line items
          </p>
          <div className="overflow-x-auto rounded-lg ring-1 ring-foreground/10">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>SKU</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Qty</TableHead>
                  <TableHead>Unit</TableHead>
                  <TableHead className="text-right">Unit Price</TableHead>
                  <TableHead className="text-right">Line Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {po.items.map((item, i) => (
                  <TableRow key={i}>
                    <TableCell className="text-muted-foreground">{item.sku ?? "—"}</TableCell>
                    <TableCell>{item.description}</TableCell>
                    <TableCell className="text-right tabular-nums">{item.quantity}</TableCell>
                    <TableCell>{item.unit ?? "—"}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {money(item.unit_price)}
                    </TableCell>
                    <TableCell className="text-right font-medium tabular-nums">
                      {money(item.line_total)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>

        <div className="flex justify-end">
          <div className="w-full max-w-xs space-y-1.5 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Subtotal</span>
              <span className="tabular-nums">{money(po.subtotal)}</span>
            </div>
            {po.discount > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Discount</span>
                <span className="tabular-nums">-{money(po.discount)}</span>
              </div>
            )}
            {po.tax > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tax</span>
                <span className="tabular-nums">{money(po.tax)}</span>
              </div>
            )}
            {po.shipping > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Shipping</span>
                <span className="tabular-nums">{money(po.shipping)}</span>
              </div>
            )}
            <div className="flex justify-between border-t pt-1.5 text-base font-semibold">
              <span>Total</span>
              <span className="tabular-nums">{money(po.total)}</span>
            </div>
          </div>
        </div>

        <div className="grid gap-6 border-t pt-4 sm:grid-cols-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Delivery terms
            </p>
            <p className="mt-1 text-sm">{po.delivery_terms ?? "Not specified"}</p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Payment terms
            </p>
            <p className="mt-1 text-sm">{po.payment_terms ?? "Not specified"}</p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Warranty
            </p>
            <p className="mt-1 text-sm">{po.warranty ?? "Not specified"}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
