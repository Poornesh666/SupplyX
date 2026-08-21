import { z } from "zod";

export const rfqFormSchema = z.object({
  title: z.string().min(3, "Title must be at least 3 characters").max(200),
  description: z.string().max(2000),
  specifications: z.string().max(2000),
  quantity: z.coerce.number().positive("Quantity must be greater than 0"),
  unit: z.string().min(1, "Unit is required").max(20),
  required_delivery_date: z
    .string()
    .min(1, "Required delivery date is required")
    .refine((value) => new Date(value) > new Date(), {
      message: "Delivery date must be in the future",
    }),
  invited_vendor_ids: z.array(z.string()).min(1, "Invite at least one vendor"),
});

export type RFQFormValues = z.infer<typeof rfqFormSchema>;

export const vendorFormSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").max(200),
  company: z.string().min(2, "Company must be at least 2 characters").max(200),
  contact: z.string().max(200),
  email: z.string().email("Enter a valid email address"),
  phone: z.string().max(30),
  reliability_score: z.coerce.number().min(0).max(100),
  quality_score: z.coerce.number().min(0).max(100),
  payment_score: z.coerce.number().min(0).max(100),
  risk_level: z.enum(["low", "medium", "high"]),
});

export type VendorFormValues = z.infer<typeof vendorFormSchema>;
