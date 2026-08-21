"use client";

import { useState } from "react";
import { CheckCircle2, XCircle } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { procurementApi } from "@/lib/procurement-api";
import type { ApprovalDecision, ApprovalResponse } from "@/types/procurement";

interface ApprovalDialogProps {
  rfqId: string;
  vendorName?: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDecided: (approval: ApprovalResponse) => void;
}

export function ApprovalDialog({
  rfqId,
  vendorName,
  open,
  onOpenChange,
  onDecided,
}: ApprovalDialogProps) {
  const [approverName, setApproverName] = useState("Procurement Manager");
  const [note, setNote] = useState("");
  const [noteError, setNoteError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<ApprovalDecision | null>(null);

  const resetAndClose = () => {
    setNote("");
    setNoteError(null);
    setSubmitting(null);
    onOpenChange(false);
  };

  const submit = async (decision: ApprovalDecision) => {
    if (decision === "rejected" && note.trim().length === 0) {
      setNoteError("A reason is required to reject this recommendation.");
      return;
    }
    setNoteError(null);
    setSubmitting(decision);
    try {
      const approval = await procurementApi.createApproval(rfqId, {
        decision,
        approver_name: approverName.trim() || "Procurement Manager",
        note: note.trim() || undefined,
      });
      toast.success(
        decision === "approved" ? "Recommendation approved" : "Recommendation rejected"
      );
      onDecided(approval);
      resetAndClose();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to record decision");
    } finally {
      setSubmitting(null);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) resetAndClose();
        else onOpenChange(next);
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Approve or reject recommendation</DialogTitle>
        </DialogHeader>
        <FieldGroup>
          {vendorName && (
            <p className="text-sm text-muted-foreground">
              Recommended vendor: <span className="font-medium text-foreground">{vendorName}</span>
            </p>
          )}
          <Field>
            <FieldLabel htmlFor="approver_name">Approver name</FieldLabel>
            <Input
              id="approver_name"
              value={approverName}
              onChange={(e) => setApproverName(e.target.value)}
              placeholder="Procurement Manager"
            />
          </Field>
          <Field>
            <FieldLabel htmlFor="note">Note (optional for approval, required for rejection)</FieldLabel>
            <Textarea
              id="note"
              value={note}
              onChange={(e) => {
                setNote(e.target.value);
                if (noteError) setNoteError(null);
              }}
              placeholder="Add context for this decision..."
              rows={3}
            />
            <FieldError errors={noteError ? [{ message: noteError }] : []} />
          </Field>
        </FieldGroup>
        <DialogFooter>
          <Button
            variant="destructive"
            disabled={submitting !== null}
            onClick={() => submit("rejected")}
          >
            <XCircle className="h-4 w-4" />
            {submitting === "rejected" ? "Rejecting..." : "Reject"}
          </Button>
          <Button disabled={submitting !== null} onClick={() => submit("approved")}>
            <CheckCircle2 className="h-4 w-4" />
            {submitting === "approved" ? "Approving..." : "Approve"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
