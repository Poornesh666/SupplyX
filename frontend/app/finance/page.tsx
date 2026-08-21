"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CircleDollarSign, Clock, Handshake, Wallet } from "lucide-react";

import { Topbar } from "@/components/layout/topbar";
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
import { procurementApi } from "@/lib/procurement-api";
import { cn } from "@/lib/utils";
import type {
  FinanceSummary,
  FinanceTransaction,
  FinanceTransactionStatus,
} from "@/types/procurement";

function money(value: number) {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

const STATUS_STYLE: Record<FinanceTransactionStatus, string> = {
  pending: "border-amber-500/40 text-amber-600 dark:text-amber-400",
  approved: "border-sky-500/40 text-sky-600 dark:text-sky-400",
  paid: "border-emerald-500/40 text-emerald-600 dark:text-emerald-400",
};

const SUMMARY_CARDS: {
  key: keyof FinanceSummary;
  label: string;
  icon: typeof Wallet;
  hint: string;
}[] = [
  {
    key: "total_procurement_spend",
    label: "Total Procurement Spend",
    icon: Wallet,
    hint: "All non-cancelled purchase orders",
  },
  {
    key: "pending_payments",
    label: "Pending Payments",
    icon: Clock,
    hint: "Draft & issued purchase orders",
  },
  {
    key: "committed_spend",
    label: "Committed Spend",
    icon: Handshake,
    hint: "Acknowledged by vendor",
  },
  {
    key: "paid_amount",
    label: "Paid Amount",
    icon: CircleDollarSign,
    hint: "Received purchase orders",
  },
];

export default function FinancePage() {
  const [summary, setSummary] = useState<FinanceSummary | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [transactions, setTransactions] = useState<FinanceTransaction[] | null>(null);
  const [transactionsError, setTransactionsError] = useState<string | null>(null);

  useEffect(() => {
    procurementApi
      .getFinanceSummary()
      .then(setSummary)
      .catch((err) =>
        setSummaryError(err instanceof Error ? err.message : "Failed to load finance summary")
      );
    procurementApi
      .listFinanceTransactions()
      .then((res) => setTransactions(res.items))
      .catch((err) =>
        setTransactionsError(
          err instanceof Error ? err.message : "Failed to load finance transactions"
        )
      );
  }, []);

  return (
    <>
      <Topbar title="Finance" />
      <main className="flex-1 space-y-6 p-6">
        <p className="text-sm text-muted-foreground">
          Procurement spend derived live from purchase order status.
        </p>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {SUMMARY_CARDS.map((card, index) => (
            <motion.div
              key={card.key}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05, ease: "easeOut" }}
            >
              <Card className="h-full transition-shadow duration-200 hover:shadow-md">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-xs font-medium text-muted-foreground">
                    {card.label}
                  </CardTitle>
                  <card.icon className="h-3.5 w-3.5 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  {summaryError && <p className="text-xs text-destructive">Unavailable</p>}
                  {!summaryError && summary === null && <Skeleton className="h-7 w-24" />}
                  {!summaryError && summary !== null && (
                    <div className="text-xl font-semibold tabular-nums">
                      {money(summary[card.key])}
                    </div>
                  )}
                  <p className="mt-1 text-xs text-muted-foreground">{card.hint}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        <Card>
          <CardContent className="p-0">
            {transactionsError && (
              <p className="p-6 text-sm text-destructive">{transactionsError}</p>
            )}
            {!transactionsError && transactions === null && (
              <div className="space-y-2 p-6">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            )}
            {transactions !== null && transactions.length === 0 && (
              <p className="p-6 text-sm text-muted-foreground">
                No transactions yet. They appear automatically once a purchase order is created.
              </p>
            )}
            {transactions !== null && transactions.length > 0 && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>PO Number</TableHead>
                    <TableHead>Vendor</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transactions.map((tx) => (
                    <TableRow key={tx.id}>
                      <TableCell className="font-medium">{tx.po_number}</TableCell>
                      <TableCell>{tx.vendor_name}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        {money(tx.amount)}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {tx.transaction_type.replace("_", " ")}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={cn(STATUS_STYLE[tx.status])}>
                          {tx.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(tx.created_at).toLocaleDateString()}
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
