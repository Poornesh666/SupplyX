"use client";

import { useEffect, useState } from "react";
import { motion, useMotionValue, useMotionValueEvent, useReducedMotion, useSpring } from "framer-motion";

import { cn } from "@/lib/utils";

export function useCountUp(value: number) {
  const prefersReducedMotion = useReducedMotion();
  const motionValue = useMotionValue(value);
  const spring = useSpring(
    motionValue,
    prefersReducedMotion
      ? { stiffness: 1000, damping: 100, mass: 0.1 }
      : { stiffness: 110, damping: 22, mass: 0.6 }
  );
  const [display, setDisplay] = useState(value);

  useEffect(() => {
    motionValue.set(value);
  }, [value, motionValue]);

  useMotionValueEvent(spring, "change", (latest) => setDisplay(latest));

  return display;
}

export function ScoreBar({
  label,
  value,
  max,
  className,
}: {
  label: string;
  value: number;
  max: number;
  className?: string;
}) {
  const percent = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  const animatedValue = useCountUp(value);

  return (
    <div className={cn("space-y-1", className)}>
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{label}</span>
        <span className="tabular-nums">
          {animatedValue.toFixed(1)} / {max}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <motion.div
          className="h-full rounded-full bg-primary"
          initial={false}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.3, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

export function TotalScoreRing({ score }: { score: number }) {
  const percent = Math.min(100, Math.max(0, score));
  const animatedScore = useCountUp(score);
  const color =
    score >= 80
      ? "text-emerald-600 dark:text-emerald-400"
      : score >= 60
        ? "text-amber-600 dark:text-amber-400"
        : "text-destructive";

  return (
    <div className="relative inline-flex h-24 w-24 items-center justify-center">
      <svg viewBox="0 0 36 36" className="h-full w-full -rotate-90">
        <circle
          cx="18"
          cy="18"
          r="16"
          fill="none"
          className="stroke-muted"
          strokeWidth="3"
        />
        <motion.circle
          cx="18"
          cy="18"
          r="16"
          fill="none"
          strokeWidth="3"
          strokeLinecap="round"
          className={color}
          stroke="currentColor"
          initial={false}
          animate={{ strokeDasharray: `${(percent / 100) * 100.5} 100.5` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </svg>
      <span className={cn("absolute text-xl font-semibold tabular-nums", color)}>
        {animatedScore.toFixed(0)}
      </span>
    </div>
  );
}
