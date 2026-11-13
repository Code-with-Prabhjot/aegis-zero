"use client";

import { useEffect, useRef } from "react";

/** Rotating dotted sphere with parallax; cheap canvas (no blur filters). */
export default function Orb({ size = 560 }: { size?: number }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const c = ref.current!;
    const ctx = c.getContext("2d")!;
    const d = Math.min(devicePixelRatio || 1, 1.5);
    c.width = size * d;
    c.height = size * d;
    ctx.setTransform(d, 0, 0, d, 0, 0);
    const still = matchMedia("(prefers-reduced-motion: reduce)").matches;

    const N = 900;
    const pts = Array.from({ length: N }, (_, i) => {
      const y = 1 - (i / (N - 1)) * 2;
      const r = Math.sqrt(1 - y * y);
      const th = i * 2.399963;
      return { x: Math.cos(th) * r, y, z: Math.sin(th) * r, s: Math.random() };
    });
    const m = { x: 0, y: 0 };
    const onMove = (e: MouseEvent) => {
      m.x = (e.clientX / innerWidth - 0.5) * 2;
      m.y = (e.clientY / innerHeight - 0.5) * 2;
    };
    addEventListener("mousemove", onMove);

    let a = 0, raf = 0, t = 0;
    const R = size * 0.36;
    const draw = () => {
      t += 0.016;
      a += 0.0035;
      ctx.clearRect(0, 0, size, size);
      const ay = a + m.x * 0.5, ax = m.y * 0.3;
      const cy = Math.cos(ay), sy = Math.sin(ay), cx = Math.cos(ax), sx = Math.sin(ax);
      for (const p of pts) {
        const x1 = p.x * cy + p.z * sy, z1 = -p.x * sy + p.z * cy;
        const y2 = p.y * cx - z1 * sx, z2 = p.y * sx + z1 * cx;
        const depth = (z2 + 1) / 2;
        const pulse = 0.6 + 0.4 * Math.sin(t * 2 + p.s * 12);
        const al = (0.12 + depth * 0.85) * pulse;
        const hue = 270 + depth * 50;
        ctx.fillStyle = `hsla(${hue},95%,${60 + depth * 20}%,${al})`;
        const rr = 0.6 + depth * 1.9;
        ctx.fillRect(size / 2 + x1 * R - rr / 2, size / 2 + y2 * R - rr / 2, rr, rr);
      }
      if (!still) raf = requestAnimationFrame(draw);
    };
    draw();
    return () => {
      cancelAnimationFrame(raf);
      removeEventListener("mousemove", onMove);
    };
  }, [size]);

  return <canvas ref={ref} style={{ width: size, height: size }} aria-hidden />;
}
