import {
  LayoutDashboard,
  FileText,
  Building2,
  ShoppingCart,
  Boxes,
  Wallet,
  BarChart3,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  group: string;
}

// "Procurement" and "Quotes" are intentionally not separate nav entries --
// RFQs is the single procurement/quote workflow entry point (quote upload,
// AI analysis, and comparison all live inside an RFQ), so duplicate links
// to the same destination were removed rather than left as dead-end stubs.
export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard, group: "Workspace" },
  { label: "RFQs", href: "/rfqs", icon: FileText, group: "Workspace" },
  { label: "Vendors", href: "/vendors", icon: Building2, group: "Supply" },
  { label: "Purchase Orders", href: "/purchase-orders", icon: ShoppingCart, group: "Supply" },
  { label: "Inventory", href: "/inventory", icon: Boxes, group: "Supply" },
  { label: "Finance", href: "/finance", icon: Wallet, group: "Insights" },
  { label: "Analytics", href: "/analytics", icon: BarChart3, group: "Insights" },
];

export const NAV_GROUPS = ["Workspace", "Supply", "Insights"] as const;
