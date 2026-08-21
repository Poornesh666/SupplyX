"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Plus } from "lucide-react";

import { Topbar } from "@/components/layout/topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { RFQStatusBadge } from "@/components/procurement/status-badge";
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
import type { RFQ } from "@/types/procurement";

export default function RFQsPage() {
  const [rfqs, setRfqs] = useState<RFQ[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    procurementApi
      .listRFQs()
      .then((res) => setRfqs(res.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load RFQs"));
  }, []);

  return (
    <>
      <Topbar title="RFQs" />
      <main className="flex-1 space-y-6 p-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Requests for quotation and their procurement decision status.
          </p>
          <Button render={<Link href="/rfqs/new" />}>
            <Plus className="h-4 w-4" />
            New RFQ
          </Button>
        </div>

        <Card>
          <CardContent className="p-0">
            {error && <p className="p-6 text-sm text-destructive">{error}</p>}
            {!error && rfqs === null && (
              <div className="space-y-2 p-6">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            )}
            {rfqs !== null && rfqs.length === 0 && (
              <p className="p-6 text-sm text-muted-foreground">
                No RFQs yet. Create your first RFQ to start the procurement workflow.
              </p>
            )}
            {rfqs !== null && rfqs.length > 0 && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>RFQ</TableHead>
                    <TableHead>Quantity</TableHead>
                    <TableHead>Required delivery</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rfqs.map((rfq, index) => (
                    <motion.tr
                      key={rfq.id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.25, delay: index * 0.04, ease: "easeOut" }}
                      className="cursor-pointer border-b transition-colors hover:bg-muted/50"
                    >
                      <TableCell>
                        <Link href={`/rfqs/${rfq.id}`} className="block">
                          <div className="font-medium hover:underline">{rfq.title}</div>
                          <div className="text-xs text-muted-foreground">
                            {rfq.rfq_number}
                          </div>
                        </Link>
                      </TableCell>
                      <TableCell>
                        {rfq.quantity} {rfq.unit}
                      </TableCell>
                      <TableCell>{rfq.required_delivery_date}</TableCell>
                      <TableCell>
                        <RFQStatusBadge status={rfq.status} />
                      </TableCell>
                    </motion.tr>
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
