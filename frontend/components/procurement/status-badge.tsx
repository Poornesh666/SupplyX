"use client";

import { AnimatePresence, motion } from "framer-motion";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { QuoteStatus, RFQStatus } from "@/types/procurement";

const RFQ_STATUS_LABEL: Record<RFQStatus, string> = {
  created: "Created",
  quotes_received: "Quotes received",
  analysis_complete: "Analysis complete",
  recommendation_ready: "Recommendation ready",
  approved: "Approved",
  rejected: "Rejected",
  po_created: "PO created",
  po_issued: "PO issued",
};

const RFQ_STATUS_STYLE: Record<RFQStatus, string> = {
  created: "border-muted-foreground/30 text-muted-foreground",
  quotes_received: "border-sky-500/40 text-sky-600 dark:text-sky-400",
  analysis_complete: "border-violet-500/40 text-violet-600 dark:text-violet-400",
  recommendation_ready: "border-emerald-500/40 text-emerald-600 dark:text-emerald-400",
  approved: "border-emerald-500/40 text-emerald-600 dark:text-emerald-400",
  rejected: "border-destructive/40 text-destructive",
  po_created: "border-amber-500/40 text-amber-600 dark:text-amber-400",
  po_issued: "border-emerald-600/50 text-emerald-700 dark:text-emerald-300",
};

export function RFQStatusBadge({ status }: { status: RFQStatus }) {
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.span
        key={status}
        initial={{ opacity: 0, y: -3 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 3 }}
        transition={{ duration: 0.18, ease: "easeOut" }}
        className="inline-flex"
      >
        <Badge variant="outline" className={cn(RFQ_STATUS_STYLE[status])}>
          {RFQ_STATUS_LABEL[status]}
        </Badge>
      </motion.span>
    </AnimatePresence>
  );
}

const QUOTE_STATUS_LABEL: Record<QuoteStatus, string> = {
  extracted: "Extracted",
  extraction_failed: "Extraction failed",
};

const QUOTE_STATUS_STYLE: Record<QuoteStatus, string> = {
  extracted: "border-emerald-500/40 text-emerald-600 dark:text-emerald-400",
  extraction_failed: "border-destructive/40 text-destructive",
};

export function QuoteStatusBadge({ status }: { status: QuoteStatus }) {
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.span
        key={status}
        initial={{ opacity: 0, y: -3 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 3 }}
        transition={{ duration: 0.18, ease: "easeOut" }}
        className="inline-flex"
      >
        <Badge variant="outline" className={cn(QUOTE_STATUS_STYLE[status])}>
          {QUOTE_STATUS_LABEL[status]}
        </Badge>
      </motion.span>
    </AnimatePresence>
  );
}
