import { api } from "@/lib/api";
import type {
  ApprovalCreateInput,
  ApprovalResponse,
  AuditEvent,
  ComparisonResponse,
  DashboardMetrics,
  FinanceSummary,
  FinanceTransaction,
  InventoryItem,
  ProcurementInsight,
  PurchaseOrder,
  Quote,
  RecommendationResponse,
  RFQ,
  ScoringWeights,
  Vendor,
} from "@/types/procurement";

export interface RFQListResponse {
  items: RFQ[];
  total: number;
}

export interface VendorListResponse {
  items: Vendor[];
  total: number;
}

export interface QuoteListResponse {
  items: Quote[];
  total: number;
}

export interface RFQCreateInput {
  title: string;
  description: string;
  specifications: string;
  quantity: number;
  unit: string;
  required_delivery_date: string;
  invited_vendor_ids: string[];
}

export interface VendorCreateInput {
  name: string;
  company: string;
  contact: string;
  email: string;
  phone: string;
  reliability_score: number;
  quality_score: number;
  payment_score: number;
  risk_level: "low" | "medium" | "high";
}

export const procurementApi = {
  listRFQs: () => api.get<RFQListResponse>("/rfqs"),
  getRFQ: (id: string) => api.get<RFQ>(`/rfqs/${id}`),
  createRFQ: (payload: RFQCreateInput) => api.post<RFQ>("/rfqs", payload),

  listVendors: () => api.get<VendorListResponse>("/vendors"),
  getVendor: (id: string) => api.get<Vendor>(`/vendors/${id}`),
  createVendor: (payload: VendorCreateInput) => api.post<Vendor>("/vendors", payload),

  listQuotes: (rfqId: string) =>
    api.get<QuoteListResponse>(`/quotes?rfq_id=${encodeURIComponent(rfqId)}`),
  uploadQuote: async (rfqId: string, vendorId: string, file: File): Promise<Quote> => {
    const formData = new FormData();
    formData.append("rfq_id", rfqId);
    formData.append("vendor_id", vendorId);
    formData.append("file", file);

    const API_BASE_URL =
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
    const response = await fetch(`${API_BASE_URL}/quotes/upload`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail ?? response.statusText);
    }
    return response.json();
  },

  getComparison: (rfqId: string) =>
    api.get<ComparisonResponse>(`/rfqs/${rfqId}/comparison`),
  getRecommendation: (rfqId: string) =>
    api.get<RecommendationResponse>(`/rfqs/${rfqId}/recommendation`),

  // ---- What-if simulator (owned by Agent 4) ----
  simulateWhatIf: (rfqId: string, weights: ScoringWeights) =>
    api.post<ComparisonResponse>(`/rfqs/${rfqId}/what-if`, { weights }),

  // ---- Dashboard intelligence (owned by Agent 4) ----
  getDashboardMetrics: () => api.get<DashboardMetrics>("/dashboard/summary"),

  // ---- Approval (owned by Agent 2/3) ----
  getApproval: (rfqId: string) =>
    api.get<ApprovalResponse | null>(`/rfqs/${rfqId}/approval`),
  createApproval: (rfqId: string, payload: ApprovalCreateInput) =>
    api.post<ApprovalResponse>(`/rfqs/${rfqId}/approval`, payload),

  // ---- Purchase orders (owned by Agent 2/3) ----
  listPurchaseOrders: () =>
    api.get<{ items: PurchaseOrder[]; total: number }>("/purchase-orders"),
  getPurchaseOrder: (id: string) =>
    api.get<PurchaseOrder>(`/purchase-orders/${id}`),
  createPurchaseOrder: (rfqId: string) =>
    api.post<PurchaseOrder>("/purchase-orders", { rfq_id: rfqId }),
  updatePurchaseOrderStatus: (id: string, status: PurchaseOrder["status"]) =>
    api.patch<PurchaseOrder>(`/purchase-orders/${id}/status`, { status }),

  // ---- Audit trail (owned by Agent 5) ----
  getAuditTrail: (rfqId: string) =>
    api.get<{ items: AuditEvent[] }>(`/rfqs/${rfqId}/audit-trail`),

  // ---- AI procurement insights (owned by Agent D) ----
  getInsights: (rfqId?: string) =>
    api.get<{ items: ProcurementInsight[] }>(
      rfqId ? `/insights?rfq_id=${encodeURIComponent(rfqId)}` : "/insights"
    ),

  // ---- Inventory (owned by Agent C) ----
  listInventory: () => api.get<{ items: InventoryItem[] }>("/inventory"),
  receiveInventory: (poId: string) =>
    api.post<{ items: InventoryItem[] }>("/inventory/receive", { po_id: poId }),

  // ---- Finance (owned by Agent C) ----
  listFinanceTransactions: () =>
    api.get<{ items: FinanceTransaction[] }>("/finance/transactions"),
  getFinanceSummary: () => api.get<FinanceSummary>("/finance/summary"),
};
