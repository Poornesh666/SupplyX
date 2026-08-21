import { FileText } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RiskList } from "@/components/procurement/risk-badge";
import { QuoteStatusBadge } from "@/components/procurement/status-badge";
import type { Quote, Vendor } from "@/types/procurement";

export function QuoteCard({ quote, vendor }: { quote: Quote; vendor: Vendor | undefined }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <div>
            <CardTitle className="text-base">{vendor?.company ?? "Unknown vendor"}</CardTitle>
            <p className="text-xs text-muted-foreground">{quote.filename}</p>
          </div>
        </div>
        <QuoteStatusBadge status={quote.status} />
      </CardHeader>
      <CardContent className="space-y-4">
        {quote.status === "extraction_failed" && (
          <p className="text-sm text-destructive">{quote.extraction_error}</p>
        )}

        {quote.extraction && quote.normalized && (
          <>
            <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-4">
              <div>
                <p className="text-xs text-muted-foreground">Calculated total</p>
                <p className="font-medium">
                  {quote.normalized.calculated_total.toLocaleString()}{" "}
                  {quote.extraction.currency ?? ""}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Delivery</p>
                <p className="font-medium">
                  {quote.extraction.delivery_days ?? "—"} days
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Warranty</p>
                <p className="font-medium">{quote.extraction.warranty ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Payment terms</p>
                <p className="font-medium">{quote.extraction.payment_terms ?? "—"}</p>
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground">
                Risks ({quote.risks.length})
              </p>
              <RiskList risks={quote.risks} />
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
