"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import type { z } from "zod";

import { Topbar } from "@/components/layout/topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { procurementApi } from "@/lib/procurement-api";
import { rfqFormSchema, type RFQFormValues } from "@/lib/schemas";
import type { Vendor } from "@/types/procurement";

export default function NewRFQPage() {
  const router = useRouter();
  const [vendors, setVendors] = useState<Vendor[]>([]);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<z.input<typeof rfqFormSchema>, unknown, RFQFormValues>({
    resolver: zodResolver(rfqFormSchema),
    defaultValues: {
      title: "",
      description: "",
      specifications: "",
      quantity: 1,
      unit: "pcs",
      required_delivery_date: "",
      invited_vendor_ids: [],
    },
  });

  useEffect(() => {
    procurementApi.listVendors().then((res) => setVendors(res.items));
  }, []);

  const selectedVendorIds = watch("invited_vendor_ids");

  const toggleVendor = (vendorId: string, checked: boolean) => {
    const next = checked
      ? [...selectedVendorIds, vendorId]
      : selectedVendorIds.filter((id) => id !== vendorId);
    setValue("invited_vendor_ids", next, { shouldValidate: true });
  };

  const onSubmit = async (values: RFQFormValues) => {
    try {
      const rfq = await procurementApi.createRFQ(values);
      toast.success(`${rfq.rfq_number} created`);
      router.push(`/rfqs/${rfq.id}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not create RFQ");
    }
  };

  return (
    <>
      <Topbar title="New RFQ" />
      <main className="flex-1 p-6">
        <Card className="mx-auto max-w-2xl">
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit(onSubmit)}>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="title">Title</FieldLabel>
                  <Input
                    id="title"
                    placeholder="e.g. Industrial Bearing Procurement"
                    {...register("title")}
                  />
                  <FieldError errors={[errors.title]} />
                </Field>

                <Field>
                  <FieldLabel htmlFor="description">Description</FieldLabel>
                  <Textarea id="description" rows={3} {...register("description")} />
                </Field>

                <Field>
                  <FieldLabel htmlFor="specifications">Specifications</FieldLabel>
                  <Textarea
                    id="specifications"
                    rows={2}
                    placeholder="e.g. 6205-2RS Industrial Bearing"
                    {...register("specifications")}
                  />
                </Field>

                <Field orientation="responsive">
                  <Field>
                    <FieldLabel htmlFor="quantity">Quantity</FieldLabel>
                    <Input id="quantity" type="number" min={1} {...register("quantity")} />
                    <FieldError errors={[errors.quantity]} />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="unit">Unit</FieldLabel>
                    <Input id="unit" placeholder="pcs" {...register("unit")} />
                    <FieldError errors={[errors.unit]} />
                  </Field>
                </Field>

                <Field>
                  <FieldLabel htmlFor="required_delivery_date">
                    Required delivery date
                  </FieldLabel>
                  <Input
                    id="required_delivery_date"
                    type="date"
                    {...register("required_delivery_date")}
                  />
                  <FieldError errors={[errors.required_delivery_date]} />
                </Field>

                <Field>
                  <FieldLabel>Invited vendors</FieldLabel>
                  {vendors.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No vendors yet — add vendors first on the Vendors page.
                    </p>
                  ) : (
                    <div className="space-y-2 rounded-md border p-3">
                      {vendors.map((vendor) => (
                        <label
                          key={vendor.id}
                          className="flex items-center gap-2 text-sm"
                        >
                          <Checkbox
                            checked={selectedVendorIds.includes(vendor.id)}
                            onCheckedChange={(checked) =>
                              toggleVendor(vendor.id, checked === true)
                            }
                          />
                          {vendor.company}
                        </label>
                      ))}
                    </div>
                  )}
                  <FieldError errors={[errors.invited_vendor_ids]} />
                </Field>
              </FieldGroup>

              <Button type="submit" className="mt-6 w-full" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create RFQ"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    </>
  );
}
