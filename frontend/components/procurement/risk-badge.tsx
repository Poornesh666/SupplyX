"use client";

import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Risk, RiskSeverity } from "@/types/procurement";

const SEVERITY_STYLES: Record<RiskSeverity, string> = {
  high: "border-destructive/40 text-destructive",
  medium: "border-amber-500/40 text-amber-600 dark:text-amber-400",
  low: "border-muted-foreground/30 text-muted-foreground",
};

const SEVERITY_ICON: Record<RiskSeverity, typeof AlertTriangle> = {
  high: AlertTriangle,
  medium: AlertCircle,
  low: Info,
};

export function RiskSeverityBadge({ severity }: { severity: RiskSeverity }) {
  const Icon = SEVERITY_ICON[severity];
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.span
        key={severity}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        transition={{ duration: 0.18, ease: "easeOut" }}
        className="inline-flex"
      >
        <Badge variant="outline" className={cn("gap-1 capitalize", SEVERITY_STYLES[severity])}>
          <Icon className="h-3 w-3" />
          {severity}
        </Badge>
      </motion.span>
    </AnimatePresence>
  );
}

export function RiskList({ risks }: { risks: Risk[] }) {
  if (risks.length === 0) {
    return <p className="text-sm text-muted-foreground">No risks detected.</p>;
  }
  return (
    <ul className="space-y-2">
      <AnimatePresence initial={false}>
        {risks.map((risk, index) => (
          <motion.li
            key={`${risk.type}-${index}`}
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2, delay: index * 0.03, ease: "easeOut" }}
            className="flex items-start gap-2 text-sm"
          >
            <RiskSeverityBadge severity={risk.severity} />
            <span className="leading-snug">{risk.description}</span>
          </motion.li>
        ))}
      </AnimatePresence>
    </ul>
  );
}
