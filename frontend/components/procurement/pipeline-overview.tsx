"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  FileSearch,
  Sparkles,
  ThumbsUp,
  ShoppingCart,
  type LucideIcon,
} from "lucide-react";

import { procurementApi } from "@/lib/procurement-api";
import type { RFQ, RFQStatus } from "@/types/procurement";

interface Stage {
  label: string;
  icon: LucideIcon;
  statuses: RFQStatus[];
}

const STAGES: Stage[] = [
  { label: "RFQ", icon: FileText, statuses: ["created"] },
  { label: "Quotes", icon: FileSearch, statuses: ["quotes_received", "analysis_complete"] },
  { label: "Recommendation", icon: Sparkles, statuses: ["recommendation_ready"] },
  { label: "Approval", icon: ThumbsUp, statuses: ["approved", "rejected"] },
  { label: "Purchase Order", icon: ShoppingCart, statuses: ["po_created", "po_issued"] },
];

export function PipelineOverview() {
  const [rfqs, setRfqs] = useState<RFQ[] | null>(null);

  useEffect(() => {
    procurementApi
      .listRFQs()
      .then((res) => setRfqs(res.items))
      .catch(() => setRfqs([]));
  }, []);

  const counts = STAGES.map(
    (stage) => rfqs?.filter((r) => stage.statuses.includes(r.status)).length ?? 0
  );

  return (
    <div className="rounded-2xl border border-border/60 bg-card p-5">
      <p className="mb-4 flex items-center gap-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">
        <span className="h-1.5 w-1.5 rounded-full bg-intelligence" />
        Live Procurement Pipeline
      </p>
      <div className="flex items-center gap-1 overflow-x-auto">
        {STAGES.map((stage, i) => {
          const Icon = stage.icon;
          const count = counts[i];
          return (
            <div key={stage.label} className="flex items-center">
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.06, ease: "easeOut" }}
                className="flex min-w-24 flex-col items-center gap-1.5 rounded-xl px-3 py-3 text-center"
              >
                <div
                  className={
                    count > 0
                      ? "flex h-9 w-9 items-center justify-center rounded-full bg-intelligence/15 text-intelligence"
                      : "flex h-9 w-9 items-center justify-center rounded-full bg-muted text-muted-foreground/50"
                  }
                >
                  <Icon className="h-4 w-4" />
                </div>
                <span className="text-lg font-semibold tabular-nums">{rfqs ? count : "—"}</span>
                <span className="text-[11px] leading-tight whitespace-nowrap text-muted-foreground">
                  {stage.label}
                </span>
              </motion.div>
              {i < STAGES.length - 1 && (
                <div className="mx-0.5 h-px w-4 shrink-0 bg-border sm:w-8" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
