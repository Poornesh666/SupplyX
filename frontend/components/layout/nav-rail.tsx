"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

import { cn } from "@/lib/utils";
import { NAV_GROUPS, NAV_ITEMS } from "@/lib/nav";

export function NavRail() {
  const pathname = usePathname();
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      {/* Desktop: floating collapsible rail */}
      <motion.aside
        onMouseEnter={() => setExpanded(true)}
        onMouseLeave={() => setExpanded(false)}
        animate={{ width: expanded ? 208 : 64 }}
        transition={{ type: "spring", stiffness: 380, damping: 34 }}
        className="fixed top-4 bottom-4 left-4 z-40 hidden flex-col overflow-hidden rounded-2xl border border-border/60 bg-card/70 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_12px_32px_-12px_rgba(0,0,0,0.18)] backdrop-blur-xl md:flex"
      >
        <div className="flex h-14 shrink-0 items-center gap-2.5 px-4">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-primary text-xs font-bold text-primary-foreground">
            SX
          </div>
          <AnimatePresence initial={false}>
            {expanded && (
              <motion.span
                initial={{ opacity: 0, x: -4 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -4 }}
                transition={{ duration: 0.15 }}
                className="whitespace-nowrap text-sm font-semibold tracking-tight"
              >
                SupplyX
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        <nav className="flex-1 space-y-3 overflow-y-auto overflow-x-hidden px-2.5 py-2">
          {NAV_GROUPS.map((group) => (
            <div key={group}>
              <AnimatePresence initial={false}>
                {expanded && (
                  <motion.p
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.12 }}
                    className="overflow-hidden px-2.5 pb-1 text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase"
                  >
                    {group}
                  </motion.p>
                )}
              </AnimatePresence>
              <div className="space-y-1">
                {NAV_ITEMS.filter((item) => item.group === group).map((item) => {
                  const isActive =
                    item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      title={!expanded ? item.label : undefined}
                      className={cn(
                        "relative flex h-10 items-center gap-3 rounded-xl px-2.5 text-sm font-medium transition-colors duration-200",
                        isActive
                          ? "text-accent-foreground"
                          : "text-muted-foreground hover:bg-accent/60 hover:text-accent-foreground"
                      )}
                    >
                      {isActive && (
                        <motion.span
                          layoutId="nav-rail-active"
                          className="absolute inset-0 rounded-xl bg-accent"
                          transition={{ type: "spring", stiffness: 420, damping: 38 }}
                        />
                      )}
                      <Icon className="relative z-10 h-[18px] w-[18px] shrink-0" />
                      <AnimatePresence initial={false}>
                        {expanded && (
                          <motion.span
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.12 }}
                            className="relative z-10 whitespace-nowrap"
                          >
                            {item.label}
                          </motion.span>
                        )}
                      </AnimatePresence>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="shrink-0 px-4 py-3 text-[10px] tracking-wide text-muted-foreground/60">
          <AnimatePresence initial={false} mode="wait">
            <motion.span
              key={expanded ? "full" : "short"}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="whitespace-nowrap"
            >
              {expanded ? "AION 2026 · Decision Intelligence" : "AION"}
            </motion.span>
          </AnimatePresence>
        </div>
      </motion.aside>

      {/* Mobile: bottom command bar */}
      <nav className="fixed inset-x-3 bottom-3 z-40 flex items-center justify-around rounded-2xl border border-border/60 bg-card/85 px-1 py-2 shadow-[0_12px_32px_-12px_rgba(0,0,0,0.25)] backdrop-blur-xl md:hidden">
        {NAV_ITEMS.slice(0, 5).map((item) => {
          const isActive =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-1 flex-col items-center gap-0.5 rounded-xl py-1.5 text-[10px] font-medium transition-colors",
                isActive ? "text-primary" : "text-muted-foreground"
              )}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
