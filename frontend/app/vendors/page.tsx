"use client";

import { useCallback, useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import type { z } from "zod";

import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { procurementApi } from "@/lib/procurement-api";
import { vendorFormSchema, type VendorFormValues } from "@/lib/schemas";
import type { RiskLevel, Vendor } from "@/types/procurement";

const RISK_STYLE: Record<RiskLevel, string> = {
  low: "border-emerald-500/40 text-emerald-600 dark:text-emerald-400",
  medium: "border-amber-500/40 text-amber-600 dark:text-amber-400",
  high: "border-destructive/40 text-destructive",
};

function VendorForm({ onCreated }: { onCreated: (vendor: Vendor) => void }) {
  const [open, setOpen] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<z.input<typeof vendorFormSchema>, unknown, VendorFormValues>({
    resolver: zodResolver(vendorFormSchema),
    defaultValues: {
      name: "",
      company: "",
      contact: "",
      email: "",
      phone: "",
      reliability_score: 70,
      quality_score: 70,
      payment_score: 70,
      risk_level: "medium",
    },
  });

  const onSubmit = async (values: VendorFormValues) => {
    try {
      const vendor = await procurementApi.createVendor(values);
      toast.success(`Vendor "${vendor.company}" created`);
      onCreated(vendor);
      reset();
      setOpen(false);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not create vendor");
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button />}>
        <Plus className="h-4 w-4" />
        Add vendor
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Add vendor</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="company">Company</FieldLabel>
              <Input id="company" {...register("company")} />
              <FieldError errors={[errors.company]} />
            </Field>
            <Field>
              <FieldLabel htmlFor="name">Contact person</FieldLabel>
              <Input id="name" {...register("name")} />
              <FieldError errors={[errors.name]} />
            </Field>
            <Field orientation="responsive">
              <Field>
                <FieldLabel htmlFor="email">Email</FieldLabel>
                <Input id="email" type="email" {...register("email")} />
                <FieldError errors={[errors.email]} />
              </Field>
              <Field>
                <FieldLabel htmlFor="phone">Phone</FieldLabel>
                <Input id="phone" {...register("phone")} />
              </Field>
            </Field>
            <Field orientation="responsive">
              <Field>
                <FieldLabel htmlFor="reliability_score">Reliability (0-100)</FieldLabel>
                <Input
                  id="reliability_score"
                  type="number"
                  min={0}
                  max={100}
                  {...register("reliability_score")}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="quality_score">Quality (0-100)</FieldLabel>
                <Input
                  id="quality_score"
                  type="number"
                  min={0}
                  max={100}
                  {...register("quality_score")}
                />
              </Field>
            </Field>
            <Field orientation="responsive">
              <Field>
                <FieldLabel htmlFor="payment_score">Payment (0-100)</FieldLabel>
                <Input
                  id="payment_score"
                  type="number"
                  min={0}
                  max={100}
                  {...register("payment_score")}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="risk_level">Risk level</FieldLabel>
                <Select
                  value={watch("risk_level")}
                  onValueChange={(value) => setValue("risk_level", value as RiskLevel)}
                >
                  <SelectTrigger id="risk_level">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
            </Field>
          </FieldGroup>
          <DialogFooter className="mt-6">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create vendor"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    procurementApi
      .listVendors()
      .then((res) => setVendors(res.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load vendors"));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <>
      <Topbar title="Vendors" />
      <main className="flex-1 space-y-6 p-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Vendor master data used for RFQ invitations and scoring baselines.
          </p>
          <VendorForm onCreated={(vendor) => setVendors((prev) => [vendor, ...(prev ?? [])])} />
        </div>

        <Card>
          <CardContent className="p-0">
            {error && <p className="p-6 text-sm text-destructive">{error}</p>}
            {!error && vendors === null && (
              <div className="space-y-2 p-6">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            )}
            {vendors !== null && vendors.length === 0 && (
              <p className="p-6 text-sm text-muted-foreground">
                No vendors yet. Add your first vendor to start inviting them to RFQs.
              </p>
            )}
            {vendors !== null && vendors.length > 0 && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Vendor</TableHead>
                    <TableHead>Contact</TableHead>
                    <TableHead>Reliability</TableHead>
                    <TableHead>Quality</TableHead>
                    <TableHead>Payment</TableHead>
                    <TableHead>Risk</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {vendors.map((vendor, index) => (
                    <motion.tr
                      key={vendor.id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.25, delay: index * 0.04, ease: "easeOut" }}
                      className="border-b transition-colors hover:bg-muted/50"
                    >
                      <TableCell>
                        <div className="font-medium">{vendor.company}</div>
                        <div className="text-xs text-muted-foreground">
                          {vendor.vendor_id}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>{vendor.name}</div>
                        <div className="text-xs text-muted-foreground">{vendor.email}</div>
                      </TableCell>
                      <TableCell>{vendor.reliability_score}</TableCell>
                      <TableCell>{vendor.quality_score}</TableCell>
                      <TableCell>{vendor.payment_score}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={RISK_STYLE[vendor.risk_level]}>
                          {vendor.risk_level}
                        </Badge>
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
