"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { PackageCheck } from "lucide-react";
import { toast } from "sonner";

import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import type { InventoryItem, PurchaseOrder } from "@/types/procurement";

const RECEIVABLE_STATUSES: PurchaseOrder["status"][] = ["issued", "acknowledged"];

function ReceiveItemsCard({ onReceived }: { onReceived: () => void }) {
  const [orders, setOrders] = useState<PurchaseOrder[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedPoId, setSelectedPoId] = useState<string | null>(null);
  const [receiving, setReceiving] = useState(false);

  const loadOrders = useCallback(() => {
    procurementApi
      .listPurchaseOrders()
      .then((res) => {
        const receivable = res.items.filter((po) => RECEIVABLE_STATUSES.includes(po.status));
        setOrders(receivable);
        setSelectedPoId((current) =>
          current && receivable.some((po) => po.id === current) ? current : null
        );
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load purchase orders")
      );
  }, []);

  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  const handleReceive = async () => {
    if (!selectedPoId) return;
    setReceiving(true);
    try {
      await procurementApi.receiveInventory(selectedPoId);
      toast.success("Inventory received against purchase order");
      setSelectedPoId(null);
      loadOrders();
      onReceived();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to receive inventory");
    } finally {
      setReceiving(false);
    }
  };

  return (
    <Card>
      <CardContent className="flex flex-wrap items-end justify-between gap-4 p-6">
        <div>
          <p className="text-sm font-medium">Receive items</p>
          <p className="text-sm text-muted-foreground">
            Pick an issued or acknowledged purchase order to receive its line items into stock.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={selectedPoId ?? undefined}
            onValueChange={(value) => setSelectedPoId(value as string)}
          >
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select a purchase order" />
            </SelectTrigger>
            <SelectContent>
              {orders !== null && orders.length === 0 && (
                <div className="px-2 py-1.5 text-sm text-muted-foreground">
                  No receivable purchase orders
                </div>
              )}
              {orders?.map((po) => (
                <SelectItem key={po.id} value={po.id}>
                  {po.po_number} · {po.vendor_name} ({po.status})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={handleReceive} disabled={!selectedPoId || receiving}>
            <PackageCheck className="h-4 w-4" />
            {receiving ? "Receiving..." : "Receive"}
          </Button>
        </div>
        {error && <p className="w-full text-sm text-destructive">{error}</p>}
      </CardContent>
    </Card>
  );
}

export default function InventoryPage() {
  const [items, setItems] = useState<InventoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    procurementApi
      .listInventory()
      .then((res) => setItems(res.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load inventory"));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <>
      <Topbar title="Inventory" />
      <main className="flex-1 space-y-6 p-6">
        <p className="text-sm text-muted-foreground">
          Stock on hand across all warehouses, kept in sync with received purchase orders.
        </p>

        <ReceiveItemsCard onReceived={load} />

        <Card>
          <CardContent className="p-0">
            {error && <p className="p-6 text-sm text-destructive">{error}</p>}
            {!error && items === null && (
              <div className="space-y-2 p-6">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            )}
            {items !== null && items.length === 0 && (
              <p className="p-6 text-sm text-muted-foreground">
                No inventory yet. Receive a purchase order above to stock your warehouse.
              </p>
            )}
            {items !== null && items.length > 0 && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>SKU</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Quantity</TableHead>
                    <TableHead className="text-right">Available</TableHead>
                    <TableHead className="text-right">Reorder Level</TableHead>
                    <TableHead>Warehouse</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((item, index) => {
                    const lowStock = item.quantity <= item.reorder_level;
                    return (
                      <motion.tr
                        key={item.id}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.25, delay: index * 0.04, ease: "easeOut" }}
                        className="border-b transition-colors hover:bg-muted/50"
                      >
                        <TableCell className="font-medium">{item.sku}</TableCell>
                        <TableCell>{item.description}</TableCell>
                        <TableCell className="text-right tabular-nums">
                          {item.quantity.toLocaleString()} {item.unit}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {item.available_quantity.toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {item.reorder_level.toLocaleString()}
                        </TableCell>
                        <TableCell className="text-muted-foreground">{item.warehouse}</TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={cn(
                              lowStock
                                ? "border-amber-500/40 text-amber-600 dark:text-amber-400"
                                : "border-emerald-500/40 text-emerald-600 dark:text-emerald-400"
                            )}
                          >
                            {lowStock ? "Low stock" : "In stock"}
                          </Badge>
                        </TableCell>
                      </motion.tr>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </main>
    </>
  );
}
