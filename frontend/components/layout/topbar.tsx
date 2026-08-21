"use client";

import { motion } from "framer-motion";

import { ApiStatusBadge } from "@/components/api-status-badge";
import { ThemeToggle } from "@/components/theme-toggle";

export function Topbar({ title }: { title: string }) {
  return (
    <header className="flex h-16 items-center justify-between border-b border-border px-6">
      <motion.h1
        key={title}
        initial={{ opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="text-lg font-semibold tracking-tight"
      >
        {title}
      </motion.h1>
      <div className="flex items-center gap-4">
        <ThemeToggle />
        <ApiStatusBadge />
      </div>
    </header>
  );
}
