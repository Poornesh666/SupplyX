export type RFQStatus =
  | "created"
  | "quotes_received"
  | "analysis_complete"
  | "recommendation_ready"
  | "approved"
  | "rejected"
  | "po_created"
  | "po_issued";

export interface RFQ {
  id: string;
  rfq_number: string;
  title: string;
  description: string;
  specifications: string;
  quantity: number;
  unit: string;
  required_delivery_date: string;
  allowed_delivery_days: number;
  invited_vendor_ids: string[];
  status: RFQStatus;
  created_at: string;
  updated_at: string;
}

export type RiskLevel = "low" | "medium" | "high";

export interface Vendor {
  id: string;
  vendor_id: string;
  name: string;
  company: string;
  contact: string;
  email: string;
  phone: string;
  reliability_score: number;
  quality_score: number;
  payment_score: number;
  risk_level: RiskLevel;
  created_at: string;
}

export interface ExtractedItem {
  sku: string | null;
  description: string;
  quantity: number;
  unit: string | null;
  unit_price: number;
}

export interface QuoteExtraction {
  vendor_name: string | null;
  quote_number: string | null;
  quote_date: string | null;
  validity_days: number | null;
  currency: string | null;
  items: ExtractedItem[];
  subtotal: number | null;
  discount: number | null;
  tax: number | null;
  shipping: number | null;
  total: number | null;
  delivery_days: number | null;
  payment_terms: string | null;
  warranty: string | null;
  moq: number | null;
  exclusions: string[];
  notes: string | null;
  risks: string[];
  missing_information: string[];
}

export interface NormalizedQuote {
  calculated_subtotal: number;
  calculated_total: number;
  document_total: number | null;
  total_matches_document: boolean;
  normalized_unit_price: number;
}

export type RiskSeverity = "low" | "medium" | "high";
export type RiskSource = "deterministic" | "ai";

export interface Risk {
  type: string;
  severity: RiskSeverity;
  description: string;
  source: RiskSource;
  affected_field: string | null;
}

export type QuoteStatus = "extracted" | "extraction_failed";

export interface Quote {
  id: string;
  rfq_id: string;
  vendor_id: string;
  filename: string;
  file_type: string;
  status: QuoteStatus;
  extraction_error: string | null;
  extraction: QuoteExtraction | null;
  normalized: NormalizedQuote | null;
  risks: Risk[];
  created_at: string;
}

export interface ScoreBreakdown {
  price: number;
  delivery: number;
  quality: number;
  reliability: number;
  payment: number;
  risk: number;
}

export interface ScoringWeights {
  price: number;
  delivery: number;
  quality: number;
  reliability: number;
  payment: number;
  risk: number;
}

export interface VendorComparisonEntry {
  vendor_id: string;
  vendor_name: string;
  quote_id: string;
  calculated_total: number;
  delivery_days: number | null;
  score: ScoreBreakdown;
  total_score: number;
  rank: number;
  risks: Risk[];
}

export interface ComparisonResponse {
  rfq_id: string;
  weights: ScoringWeights;
  entries: VendorComparisonEntry[];
  lowest_price_vendor_id: string | null;
  recommended_vendor_id: string | null;
}

export type Confidence = "low" | "medium" | "high";

export interface RecommendationExplanation {
  recommendation_summary: string;
  why_recommended: string[];
  key_strengths: string[];
  key_risks: string[];
  tradeoffs: string[];
  alternative_vendor: string | null;
  confidence: Confidence;
  explanation: string;
}

export interface RecommendationResponse {
  rfq_id: string;
  recommended_vendor_id: string;
  recommended_vendor_name: string;
  recommended_score: number;
  alternative_vendor_id: string | null;
  alternative_vendor_name: string | null;
  alternative_score: number | null;
  potential_savings: number | null;
  explanation: RecommendationExplanation;
  generated_at: string;
}

// ---- Approval (P1) ----

export type ApprovalDecision = "approved" | "rejected";

export interface ApprovalResponse {
  id: string;
  rfq_id: string;
  decision: ApprovalDecision;
  approver_name: string;
  note: string | null;
  recommended_vendor_id: string;
  recommended_vendor_name: string;
  recommended_score: number;
  decided_at: string;
}

export interface ApprovalCreateInput {
  decision: ApprovalDecision;
  approver_name: string;
  note?: string;
}

// ---- Purchase Order (P1) ----

export type PurchaseOrderStatus =
  | "draft"
  | "issued"
  | "acknowledged"
  | "received"
  | "cancelled";

export interface PurchaseOrderItem {
  sku: string | null;
  description: string;
  quantity: number;
  unit: string | null;
  unit_price: number;
  line_total: number;
}

export interface PurchaseOrder {
  id: string;
  po_number: string;
  rfq_id: string;
  rfq_number: string;
  vendor_id: string;
  vendor_name: string;
  items: PurchaseOrderItem[];
  subtotal: number;
  discount: number;
  tax: number;
  shipping: number;
  total: number;
  delivery_terms: string | null;
  payment_terms: string | null;
  warranty: string | null;
  expected_delivery_date: string | null;
  status: PurchaseOrderStatus;
  created_at: string;
}

// ---- What-if simulator (P2) ----

export interface WhatIfRequest {
  weights: ScoringWeights;
}

// ---- Dashboard intelligence (P2) ----

export interface DashboardMetrics {
  active_rfqs: number;
  quotes_analyzed: number;
  risks_detected: number;
  potential_savings: number;
  pending_approvals: number;
}

// ---- Audit trail (P2) ----

export type AuditEventType =
  | "rfq_created"
  | "quote_uploaded"
  | "quote_analyzed"
  | "quote_extraction_failed"
  | "risk_detected"
  | "recommendation_generated"
  | "rfq_approved"
  | "rfq_rejected"
  | "po_created"
  | "po_issued"
  | "po_acknowledged"
  | "po_received"
  | "po_cancelled"
  | "inventory_received"
  | "finance_transaction_created";

export interface AuditEvent {
  id: string;
  rfq_id: string;
  event_type: AuditEventType;
  description: string;
  actor: string | null;
  created_at: string;
}

// ---- AI procurement insights (P2) ----

export interface ProcurementInsight {
  id: string;
  rfq_id: string | null;
  summary: string;
  category: "risk" | "savings" | "quality" | "general";
}

// ---- Inventory (owned by Agent C) ----

export interface InventoryItem {
  id: string;
  sku: string;
  description: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  reorder_level: number;
  unit: string;
  warehouse: string;
  updated_at: string;
}

export interface ReceiveInventoryInput {
  po_id: string;
}

// ---- Finance (owned by Agent C) ----

export type FinanceTransactionType = "po_commitment" | "payment" | "refund";
export type FinanceTransactionStatus = "pending" | "approved" | "paid";

export interface FinanceTransaction {
  id: string;
  po_id: string;
  po_number: string;
  vendor_id: string;
  vendor_name: string;
  amount: number;
  transaction_type: FinanceTransactionType;
  status: FinanceTransactionStatus;
  created_at: string;
}

export interface FinanceSummary {
  total_procurement_spend: number;
  pending_payments: number;
  paid_amount: number;
  committed_spend: number;
}
