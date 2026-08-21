"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, FileSearch, ShieldCheck, Sparkles, UploadCloud, XCircle } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { procurementApi } from "@/lib/procurement-api";
import { cn } from "@/lib/utils";
import type { Quote, Vendor } from "@/types/procurement";

const ACCEPTED_EXTENSIONS = ".pdf,.xlsx,.xls,.csv";

type Stage = "idle" | "uploading" | "extracting" | "validating" | "analyzing" | "complete" | "failed";

const STAGE_STEPS: { key: Exclude<Stage, "idle" | "complete" | "failed">; label: string; icon: typeof UploadCloud }[] = [
  { key: "uploading", label: "Uploading", icon: UploadCloud },
  { key: "extracting", label: "Extracting", icon: FileSearch },
  { key: "validating", label: "Validating", icon: ShieldCheck },
  { key: "analyzing", label: "Analyzing", icon: Sparkles },
];

const STAGE_LABEL: Record<Stage, string> = {
  idle: "Drop a vendor quote or click to browse",
  uploading: "Uploading file...",
  extracting: "Extracting quote data...",
  validating: "Validating structured data...",
  analyzing: "AI analyzing risks & pricing...",
  complete: "Quote analyzed successfully",
  failed: "Extraction failed",
};

export function QuoteUploadForm({
  rfqId,
  vendors,
  onUploaded,
}: {
  rfqId: string;
  vendors: Vendor[];
  onUploaded: (quote: Quote) => void;
}) {
  const [vendorId, setVendorId] = useState<string>("");
  const [stage, setStage] = useState<Stage>("idle");
  const [fileName, setFileName] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const timersRef = useRef<number[]>([]);
  const isMountedRef = useRef(true);

  const clearTimers = () => {
    timersRef.current.forEach((id) => window.clearTimeout(id));
    timersRef.current = [];
  };

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      clearTimers();
    };
  }, []);

  const isBusy = stage !== "idle" && stage !== "complete" && stage !== "failed";

  const processFile = useCallback(
    async (file: File) => {
      if (!vendorId) {
        toast.error("Select which vendor this quote is from first");
        return;
      }

      setFileName(file.name);
      setStage("uploading");
      clearTimers();

      // The backend extracts the quote synchronously in a single request, so
      // there is no real progress to poll. We stage timed reveals purely for
      // visual feedback while the actual request is in flight, then resolve
      // to the real outcome once the response arrives.
      timersRef.current.push(
        window.setTimeout(() => isMountedRef.current && setStage("extracting"), 500)
      );
      timersRef.current.push(
        window.setTimeout(() => isMountedRef.current && setStage("validating"), 1100)
      );
      timersRef.current.push(
        window.setTimeout(() => isMountedRef.current && setStage("analyzing"), 1700)
      );

      let outcome: "complete" | "failed" = "complete";
      try {
        const quote = await procurementApi.uploadQuote(rfqId, vendorId, file);
        clearTimers();
        outcome = quote.status === "extracted" ? "complete" : "failed";
        if (isMountedRef.current) setStage(outcome);
        if (quote.status === "extracted") {
          toast.success(`${file.name} extracted successfully`);
        } else {
          toast.error(`${file.name}: ${quote.extraction_error ?? "extraction failed"}`);
        }
        onUploaded(quote);
      } catch (error) {
        clearTimers();
        outcome = "failed";
        if (isMountedRef.current) setStage("failed");
        toast.error(error instanceof Error ? error.message : "Upload failed");
      } finally {
        const resetDelay = outcome === "failed" ? 2600 : 1800;
        timersRef.current.push(
          window.setTimeout(() => isMountedRef.current && setStage("idle"), resetDelay)
        );
      }
    },
    [rfqId, vendorId, onUploaded]
  );

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    await processFile(file);
  };

  const handleDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    if (isBusy) return;
    const file = event.dataTransfer.files?.[0];
    if (!file) return;
    await processFile(file);
  };

  const StatusIcon =
    stage === "complete" ? CheckCircle2 : stage === "failed" ? XCircle : UploadCloud;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Select value={vendorId} onValueChange={(value) => setVendorId(value ?? "")} disabled={isBusy}>
          <SelectTrigger className="sm:w-64">
            <SelectValue placeholder="Select vendor" />
          </SelectTrigger>
          <SelectContent>
            {vendors.map((vendor) => (
              <SelectItem key={vendor.id} value={vendor.id}>
                {vendor.company}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="text-xs text-muted-foreground">PDF, XLSX, XLS, or CSV</span>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS}
        className="hidden"
        onChange={handleFileChange}
      />

      <div
        role="button"
        tabIndex={0}
        onClick={() => !isBusy && fileInputRef.current?.click()}
        onKeyDown={(event) => {
          if ((event.key === "Enter" || event.key === " ") && !isBusy) {
            event.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        onDragOver={(event) => {
          event.preventDefault();
          if (!isBusy) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={cn(
          "flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed px-6 py-8 text-center transition-colors duration-200",
          isBusy ? "cursor-wait" : "cursor-pointer",
          isDragging
            ? "border-primary/60 bg-primary/5"
            : stage === "complete"
              ? "border-emerald-500/40 bg-emerald-500/5"
              : stage === "failed"
                ? "border-destructive/40 bg-destructive/5"
                : "border-border hover:border-primary/40 hover:bg-muted/40"
        )}
      >
        <motion.div
          key={stage}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-full",
            stage === "complete"
              ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
              : stage === "failed"
                ? "bg-destructive/10 text-destructive"
                : "bg-muted text-muted-foreground"
          )}
        >
          <StatusIcon className={cn("h-5 w-5", isBusy && "animate-pulse")} />
        </motion.div>

        <div className="space-y-1">
          <p className="text-sm font-medium" aria-live="polite">
            {STAGE_LABEL[stage]}
          </p>
          {fileName && stage !== "idle" && (
            <p className="text-xs text-muted-foreground">{fileName}</p>
          )}
        </div>

        <AnimatePresence>
          {isBusy && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-2"
            >
              {STAGE_STEPS.map((step) => {
                const stepIndex = STAGE_STEPS.findIndex((s) => s.key === step.key);
                const currentIndex = STAGE_STEPS.findIndex((s) => s.key === stage);
                const isDone = stepIndex < currentIndex;
                const isCurrent = step.key === stage;
                return (
                  <span
                    key={step.key}
                    className={cn(
                      "h-1.5 w-6 rounded-full transition-colors duration-300",
                      isDone || isCurrent ? "bg-primary" : "bg-muted"
                    )}
                  />
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>

        {!isBusy && stage === "idle" && (
          <Button type="button" variant="outline" size="sm" tabIndex={-1}>
            <UploadCloud className="h-4 w-4" />
            Upload vendor quote
          </Button>
        )}
      </div>
    </div>
  );
}
