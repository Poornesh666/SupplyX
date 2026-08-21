"use client";

import {
  Component,
  Suspense,
  useMemo,
  useRef,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import { useTheme } from "next-themes";
import * as THREE from "three";

/**
 * Purely decorative 3D node-graph representing the procurement decision
 * pipeline: RFQ -> Vendors -> Quotes -> Risk -> Score -> Recommendation -> PO.
 *
 * No business data is rendered inside the canvas -- it is an ambient
 * visualization only. Safe to drop into any page; it lazy-mounts, respects
 * `prefers-reduced-motion`, and falls back to a static gradient if WebGL is
 * unavailable or the canvas fails to render.
 */

type PipelineNode = {
  id: string;
  position: [number, number, number];
  radius: number;
  colorLight: string;
  colorDark: string;
  phase: number;
};

type Edge = [string, string];

// Main pipeline spine, left to right, plus a few satellite nodes that fan
// in/out to suggest multiple vendors and quotes feeding the engine.
const NODES: PipelineNode[] = [
  { id: "rfq", position: [-4.4, 0.3, 0], radius: 0.26, colorLight: "#64748b", colorDark: "#94a3b8", phase: 0 },
  { id: "vendors", position: [-2.9, 0.65, 0.2], radius: 0.22, colorLight: "#64748b", colorDark: "#94a3b8", phase: 0.6 },
  { id: "vendor-a", position: [-3.4, 1.55, -0.5], radius: 0.13, colorLight: "#94a3b8", colorDark: "#cbd5e1", phase: 1.1 },
  { id: "vendor-b", position: [-2.5, 1.7, 0.9], radius: 0.13, colorLight: "#94a3b8", colorDark: "#cbd5e1", phase: 1.7 },
  { id: "quotes", position: [-1.3, -0.35, -0.1], radius: 0.22, colorLight: "#0ea5e9", colorDark: "#38bdf8", phase: 2.1 },
  { id: "quote-a", position: [-1.9, -1.25, 0.6], radius: 0.12, colorLight: "#7dd3fc", colorDark: "#7dd3fc", phase: 2.6 },
  { id: "risk", position: [0.4, 0.55, 0.3], radius: 0.2, colorLight: "#f59e0b", colorDark: "#fbbf24", phase: 3.1 },
  { id: "score", position: [2.1, -0.25, -0.3], radius: 0.22, colorLight: "#64748b", colorDark: "#cbd5e1", phase: 3.6 },
  { id: "recommendation", position: [3.7, 0.45, 0.15], radius: 0.24, colorLight: "#10b981", colorDark: "#34d399", phase: 4.1 },
  { id: "po", position: [5.1, -0.15, 0], radius: 0.24, colorLight: "#10b981", colorDark: "#6ee7b7", phase: 4.6 },
];

const EDGES: Edge[] = [
  ["rfq", "vendors"],
  ["vendor-a", "vendors"],
  ["vendor-b", "vendors"],
  ["vendors", "quotes"],
  ["quote-a", "quotes"],
  ["quotes", "risk"],
  ["risk", "score"],
  ["score", "recommendation"],
  ["recommendation", "po"],
];

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

function subscribeReducedMotion(callback: () => void) {
  const query = window.matchMedia(REDUCED_MOTION_QUERY);
  query.addEventListener("change", callback);
  return () => query.removeEventListener("change", callback);
}

function getReducedMotionSnapshot() {
  return window.matchMedia(REDUCED_MOTION_QUERY).matches;
}

function getReducedMotionServerSnapshot() {
  return false;
}

function usePrefersReducedMotion() {
  return useSyncExternalStore(
    subscribeReducedMotion,
    getReducedMotionSnapshot,
    getReducedMotionServerSnapshot
  );
}

function isWebGLAvailable() {
  try {
    const canvas = document.createElement("canvas");
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext("webgl") || canvas.getContext("experimental-webgl"))
    );
  } catch {
    return false;
  }
}

// Mirrors the mount-detection pattern used by theme-toggle.tsx: report a
// stable value during SSR/hydration and the real client value once mounted,
// without a setState-in-effect cascade.
const emptySubscribe = () => () => {};

function useHasMounted() {
  return useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );
}

function NodeMesh({ node, dark, reducedMotion }: { node: PipelineNode; dark: boolean; reducedMotion: boolean }) {
  const color = dark ? node.colorDark : node.colorLight;
  const materialRef = useRef<THREE.MeshStandardMaterial>(null);
  const elapsed = useRef(0);

  useFrame((_, delta) => {
    if (!materialRef.current) return;
    if (!reducedMotion) elapsed.current += delta;
    const pulse = 0.85 + Math.sin(elapsed.current * 0.8 + node.phase) * 0.25;
    materialRef.current.emissiveIntensity = pulse;
  });

  return (
    <group position={node.position}>
      <mesh>
        <sphereGeometry args={[node.radius, 24, 24]} />
        <meshStandardMaterial
          ref={materialRef}
          color={color}
          emissive={color}
          emissiveIntensity={1}
          roughness={0.4}
          metalness={0.15}
        />
      </mesh>
      <mesh scale={2.1}>
        <sphereGeometry args={[node.radius, 16, 16]} />
        <meshBasicMaterial color={color} transparent opacity={0.14} depthWrite={false} />
      </mesh>
      <mesh scale={3.2}>
        <sphereGeometry args={[node.radius, 16, 16]} />
        <meshBasicMaterial color={color} transparent opacity={0.05} depthWrite={false} />
      </mesh>
    </group>
  );
}

function SceneGraph({ dark, reducedMotion }: { dark: boolean; reducedMotion: boolean }) {
  const groupRef = useRef<THREE.Group>(null);
  const rotationY = useRef(0);
  const lineColor = dark ? "#64748b" : "#94a3b8";

  const nodeMap = useMemo(() => new Map(NODES.map((node) => [node.id, node])), []);

  useFrame((state, delta) => {
    const group = groupRef.current;
    if (!group) return;

    if (!reducedMotion) {
      rotationY.current += delta * 0.045;
    }

    const parallaxX = state.pointer.y * 0.1;
    const parallaxY = state.pointer.x * 0.18;

    group.rotation.y = THREE.MathUtils.lerp(group.rotation.y, rotationY.current + parallaxY, 0.04);
    group.rotation.x = THREE.MathUtils.lerp(group.rotation.x, parallaxX, 0.04);
  });

  return (
    <group ref={groupRef}>
      {EDGES.map(([fromId, toId]) => {
        const from = nodeMap.get(fromId);
        const to = nodeMap.get(toId);
        if (!from || !to) return null;
        return (
          <Line
            key={`${fromId}-${toId}`}
            points={[from.position, to.position]}
            color={lineColor}
            transparent
            opacity={0.28}
            lineWidth={1}
          />
        );
      })}
      {NODES.map((node) => (
        <NodeMesh key={node.id} node={node} dark={dark} reducedMotion={reducedMotion} />
      ))}
    </group>
  );
}

function SceneFallback() {
  return (
    <div
      aria-hidden
      className="h-full w-full rounded-2xl bg-[radial-gradient(circle_at_30%_35%,color-mix(in_oklch,var(--muted-foreground)_18%,transparent),transparent_60%),radial-gradient(circle_at_70%_65%,color-mix(in_oklch,var(--primary)_12%,transparent),transparent_55%)] motion-safe:animate-pulse motion-reduce:animate-none"
      style={{ animationDuration: "6s" }}
    />
  );
}

class SceneErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) return <SceneFallback />;
    return this.props.children;
  }
}

export function ProcurementIntelligenceScene({ className }: { className?: string }) {
  const { resolvedTheme } = useTheme();
  const reducedMotion = usePrefersReducedMotion();
  const hasMounted = useHasMounted();
  const webglOk = useMemo(() => (hasMounted ? isWebGLAvailable() : null), [hasMounted]);

  const dark = resolvedTheme === "dark";

  return (
    <div className={className ?? "h-72 w-full sm:h-96"}>
      {webglOk === false ? (
        <SceneFallback />
      ) : (
        <SceneErrorBoundary>
          <Suspense fallback={<SceneFallback />}>
            {webglOk && (
              <Canvas
                dpr={[1, 1.5]}
                gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
                camera={{ position: [0, 0, 8.5], fov: 42 }}
                style={{ background: "transparent" }}
              >
                <ambientLight intensity={0.6} />
                <pointLight position={[4, 4, 6]} intensity={0.8} color={dark ? "#7dd3fc" : "#ffffff"} />
                <pointLight position={[-4, -3, 4]} intensity={0.5} color={dark ? "#34d399" : "#e2e8f0"} />
                <SceneGraph dark={dark} reducedMotion={reducedMotion} />
              </Canvas>
            )}
          </Suspense>
        </SceneErrorBoundary>
      )}
    </div>
  );
}

export default ProcurementIntelligenceScene;
