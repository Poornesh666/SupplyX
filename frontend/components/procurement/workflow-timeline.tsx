import { Check, X } from "lucide-react";

import { cn } from "@/lib/utils";
import type { RFQStatus } from "@/types/procurement";

interface StageDef {
  key: string;
  label: string;
}

const STAGES: StageDef[] = [
  { key: "created", label: "RFQ Created" },
  { key: "quotes", label: "Quotes" },
  { key: "analysis", label: "Analysis" },
  { key: "recommendation", label: "Recommendation" },
  { key: "approval", label: "Approval" },
  { key: "po", label: "Purchase Order" },
];

// Index (0-5) of the stage each RFQStatus corresponds to.
const STATUS_STAGE_INDEX: Record<RFQStatus, number> = {
  created: 0,
  quotes_received: 1,
  analysis_complete: 2,
  recommendation_ready: 3,
  approved: 4,
  rejected: 4,
  po_created: 5,
  po_issued: 5,
};

export function WorkflowTimeline({ status }: { status: RFQStatus }) {
  const currentIndex = STATUS_STAGE_INDEX[status];
  const isRejected = status === "rejected";
  // The approval/PO stages are only fully "done" (checkmark) once we've moved past them.
  const isFullyComplete = status === "po_issued";

  return (
    <div className="flex w-full items-start overflow-x-auto pb-1">
      {STAGES.map((stage, i) => {
        const isCurrent = i === currentIndex;
        const isDone = i < currentIndex || (isFullyComplete && i <= currentIndex);
        const isRejectedStage = isCurrent && isRejected;
        const isLast = i === STAGES.length - 1;

        return (
          <div key={stage.key} className={cn("flex items-center", !isLast && "flex-1")}>
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 text-xs font-semibold transition-colors",
                  isRejectedStage &&
                    "border-destructive bg-destructive/10 text-destructive",
                  !isRejectedStage &&
                    isDone &&
                    "border-emerald-500 bg-emerald-500 text-white dark:border-emerald-400 dark:bg-emerald-400 dark:text-emerald-950",
                  !isRejectedStage &&
                    isCurrent &&
                    !isDone &&
                    "border-primary bg-primary/10 text-primary",
                  !isRejectedStage &&
                    !isDone &&
                    !isCurrent &&
                    "border-muted-foreground/30 text-muted-foreground"
                )}
              >
                {isRejectedStage ? (
                  <X className="h-3.5 w-3.5" />
                ) : isDone ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  i + 1
                )}
              </div>
              <span
                className={cn(
                  "whitespace-nowrap text-[11px] font-medium",
                  isRejectedStage && "text-destructive",
                  !isRejectedStage && (isDone || isCurrent)
                    ? "text-foreground"
                    : "text-muted-foreground"
                )}
              >
                {stage.label}
              </span>
            </div>
            {!isLast && (
              <div
                className={cn(
                  "mx-2 mt-3.5 h-0.5 flex-1 rounded-full transition-colors",
                  i < currentIndex || (isFullyComplete && i < currentIndex + 1)
                    ? "bg-emerald-500 dark:bg-emerald-400"
                    : "bg-muted"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
