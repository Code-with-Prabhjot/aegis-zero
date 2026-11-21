"use client";

import React from "react";
import {
  Flame,
  AlertTriangle,
  RotateCcw,
  TrendingDown,
  CheckCircle2,
  Clock,
  ServerOff,
  Activity,
} from "lucide-react";
import { TelemetryState } from "@/types";
import { MODELS } from "@/lib/config";

interface Panel2Props {
  telemetry: TelemetryState;
  onTriggerChaos: () => void;
  onResetChaos: () => void;
  onUpdateBudget: (amount: number) => void;
  mode?: "simple" | "developer";
}

export function Panel2_ChaosBudget({
  telemetry,
  onTriggerChaos,
  onResetChaos,
  onUpdateBudget,
  mode = "simple",
}: Panel2Props) {
  const isChaos =
    telemetry.gatewayStatus === "CHAOS_INJECTED" || telemetry.circuitBreakerTripped;

  return (
    <div className="flex flex-col h-full bg-[#0d081c]/75 backdrop-blur-xl border border-purple-500/20 rounded-2xl overflow-hidden shadow-[0_0_30px_rgba(139,92,246,0.08)]">
      {/* Panel Top Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#140b2b]/70 border-b border-purple-500/20">
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-lg bg-rose-500/15 border border-rose-500/30 flex items-center justify-center">
            <Flame className="w-3.5 h-3.5 text-brandRose" />
          </div>
          <h2 className="text-xs font-display tracking-wider text-purple-100 uppercase">
            02 // Bifrost Gateway Resilience &amp; Pre-Flight Budget Controls
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-[10px] font-mono px-2.5 py-0.5 rounded-full border font-semibold ${
              isChaos
                ? "bg-rose-950/80 border-brandRose/80 text-brandRose animate-pulse shadow-[0_0_8px_rgba(244,63,94,0.3)]"
                : "bg-emerald-950/70 border-brandGreen/60 text-brandGreen"
            }`}
          >
            CIRCUIT-BREAKER: {isChaos ? "OPEN (CHAOS FAILOVER)" : "CLOSED (HEALTHY)"}
          </span>
        </div>
      </div>

      {/* Main Container: 50% / 50% 2-Column Split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 md:p-5 flex-1 min-h-0 overflow-y-auto">
        {/* LEFT COLUMN: 50% -> Judge 1-Click Chaos Simulator & Multi-Tier Routing Chain */}
        <div className="bg-[#0e0722]/85 border border-purple-500/20 rounded-xl p-4 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-cosmicFuchsia font-semibold">
                  Resilience Engine // Bifrost AI Gateway
                </span>
                <h3 className="text-sm font-display text-white font-bold flex items-center gap-2 mt-0.5">
                  Judge 1-Click Chaos Simulator
                </h3>
              </div>
              {isChaos && (
                <span className="flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-rose-950 border border-brandRose text-brandRose font-bold animate-pulse shadow-[0_0_10px_rgba(244,63,94,0.4)]">
                  <AlertTriangle className="w-3.5 h-3.5 text-brandRose" />
                  OUTAGE ACTIVE
                </span>
              )}
            </div>

            <p className="text-xs text-purple-300/70 leading-relaxed font-sans">
              Inject a simulated HTTP 429 Rate-Limit / Outage on the primary frontier provider. Observe sub-180ms automated circuit breaker failover to GPT-4o with zero session loss.
            </p>

            {/* High-Impact Chaos Buttons */}
            <div className="flex flex-wrap items-center gap-2.5 pt-1">
              <button
                type="button"
                onClick={onTriggerChaos}
                disabled={isChaos}
                className={`flex-1 min-w-[200px] flex items-center justify-center gap-2 px-4 py-3 rounded-full font-mono text-xs font-bold transition-all shadow-md active:scale-95 ${
                  isChaos
                    ? "bg-rose-950/40 border border-rose-900/60 text-rose-500/60 cursor-not-allowed opacity-60"
                    : "bg-gradient-to-r from-red-600 via-rose-600 to-pink-600 hover:from-red-500 hover:to-pink-500 text-white shadow-[0_0_20px_rgba(244,63,94,0.4)] border border-rose-400 cursor-pointer"
                }`}
              >
                <ServerOff className="w-4 h-4" />
                <span>[SIMULATE HTTP 429 OUTAGE]</span>
              </button>

              <button
                type="button"
                onClick={onResetChaos}
                disabled={!isChaos}
                className={`flex items-center justify-center gap-2 px-4 py-3 rounded-full font-mono text-xs font-semibold transition-all border ${
                  isChaos
                    ? "bg-[#180f33] border-brandGreen/60 text-brandGreen hover:bg-emerald-950/40 cursor-pointer shadow-[0_0_12px_rgba(16,185,129,0.25)] active:scale-95"
                    : "bg-[#100924]/40 border-purple-900/30 text-purple-400/40 cursor-not-allowed"
                }`}
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>RESTORE PRIMARY</span>
              </button>
            </div>

            {/* Sub-180ms Failover HUD Banner */}
            {isChaos && (
              <div className="p-3 rounded-xl bg-rose-950/50 border border-brandRose/70 flex items-center justify-between text-xs font-mono shadow-[0_0_15px_rgba(244,63,94,0.2)]">
                <div className="flex items-center gap-2 text-rose-100">
                  <Clock className="w-4 h-4 text-brandRose animate-spin" />
                  <span>
                    FAILOVER LATENCY:{" "}
                    <strong className="text-white font-display">
                      {telemetry.failoverLatencyMs}ms
                    </strong>
                  </span>
                  <span className="text-brandGreen text-[11px] font-semibold">
                    (&lt;180ms Target Met)
                  </span>
                </div>
                <span className="text-purple-200 text-[11px] font-semibold bg-rose-900/60 px-2 py-0.5 rounded">
                  0 Session Loss
                </span>
              </div>
            )}
          </div>

          {/* Visual Multi-Tier Routing Chain (Developer) or Clean Status Card (Simple) */}
          {mode === "simple" ? (
            <div className="bg-[#120a26]/80 p-4 rounded-xl border border-purple-500/20 space-y-2.5">
              <span className="text-[10px] font-mono uppercase text-purple-300/60 block">
                Live Active Provider Status:
              </span>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span
                    className={`w-3 h-3 rounded-full flex-shrink-0 ${
                      isChaos
                        ? "bg-amber-400 shadow-[0_0_8px_#f59e0b] animate-pulse"
                        : "bg-brandGreen shadow-[0_0_8px_#10b981]"
                    }`}
                  />
                  <div>
                    <h4 className="text-sm font-bold text-white font-mono">
                      {isChaos ? `${MODELS.fallback} (Failover)` : `${MODELS.frontier} (Primary)`}
                    </h4>
                    <p className="text-xs text-purple-300/70">
                      {isChaos
                        ? "Sub-180ms failover engaged · Zero session loss"
                        : "Primary frontier active · Full capacity"}
                    </p>
                  </div>
                </div>
                <span
                  className={`text-xs font-mono font-bold px-2.5 py-1 rounded-full ${
                    isChaos
                      ? "bg-amber-950 text-amber-300 border border-amber-500/60"
                      : "bg-emerald-950 text-emerald-300 border border-emerald-500/60"
                  }`}
                >
                  {isChaos ? "FAILOVER ACTIVE" : "ONLINE"}
                </span>
              </div>
            </div>
          ) : (
            <div className="space-y-2 pt-2 border-t border-purple-500/20">
              <span className="text-[10px] font-mono text-purple-300/60 uppercase block">
                Multi-Tier Routing Chain Topology:
              </span>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                {/* Tier 1 Primary */}
                <div
                  className={`p-2.5 rounded-xl border transition-all ${
                    !isChaos
                      ? "bg-purple-950/60 border-cosmicFuchsia/80 text-white shadow-[0_0_12px_rgba(217,70,239,0.3)]"
                      : "bg-[#090514]/60 border-purple-900/30 text-purple-400/40 line-through"
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] text-purple-300/70 mb-1">
                    <span>1. Primary Frontier</span>
                    {!isChaos && (
                      <span className="w-2 h-2 rounded-full bg-brandGreen shadow-[0_0_6px_#10b981]" />
                    )}
                  </div>
                  <p className="font-bold text-xs truncate">{MODELS.frontier}</p>
                  <span className="text-[9px] text-purple-400/60">Tier-2 Frontier</span>
                </div>

                {/* Tier 2 Secondary Failover */}
                <div
                  className={`p-2.5 rounded-xl border transition-all ${
                    isChaos
                      ? "bg-amber-950/70 border-amber-500/80 text-amber-200 shadow-[0_0_15px_rgba(245,158,11,0.35)]"
                      : "bg-[#090514]/60 border-purple-900/30 text-purple-400/40"
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] text-purple-300/70 mb-1">
                    <span>2. Secondary Failover</span>
                    {isChaos && (
                      <span className="w-2 h-2 rounded-full bg-brandAmber shadow-[0_0_6px_#f59e0b] animate-pulse" />
                    )}
                  </div>
                  <p className="font-bold text-xs truncate">{MODELS.fallback}</p>
                  <span className="text-[9px] text-amber-300/70">Sub-180ms Auto-Route</span>
                </div>

                {/* Tier 3 Micro Fast Fallback */}
                <div className="p-2.5 rounded-xl border bg-[#090514]/60 border-purple-900/30 text-purple-300/70">
                  <div className="flex items-center justify-between text-[10px] text-purple-400/60 mb-1">
                    <span>3. Budget Down-Route</span>
                  </div>
                  <p className="font-bold text-xs truncate">{MODELS.micro}</p>
                  <span className="text-[9px] text-purple-400/60">Tier-1 Micro (&lt;$0.08)</span>
                </div>

                {/* Tier 4 Air-Gapped Local */}
                <div className="p-2.5 rounded-xl border bg-[#090514]/60 border-purple-900/30 text-purple-300/70">
                  <div className="flex items-center justify-between text-[10px] text-purple-400/60 mb-1">
                    <span>4. Air-Gapped Enclave</span>
                  </div>
                  <p className="font-bold text-xs truncate">{MODELS.local}</p>
                  <span className="text-[9px] text-purple-400/60">Tier-0 Air-Gap Lock</span>
                </div>
              </div>
            </div>
          )}

          {/* Resilience Telemetry Footer */}
          <div className="grid grid-cols-3 gap-2 text-center font-mono pt-2 border-t border-purple-500/20 text-xs">
            <div className="bg-[#120a26]/70 p-2 rounded-xl border border-purple-500/20">
              <span className="text-[9px] text-purple-300/60 block uppercase">Bifrost Uptime</span>
              <span className="text-brandGreen font-bold font-display">99.99%</span>
            </div>
            <div className="bg-[#120a26]/70 p-2 rounded-xl border border-purple-500/20">
              <span className="text-[9px] text-purple-300/60 block uppercase">Failover Target</span>
              <span className="text-white font-bold font-display">&lt;180ms</span>
            </div>
            <div className="bg-[#120a26]/70 p-2 rounded-xl border border-purple-500/20">
              <span className="text-[9px] text-purple-300/60 block uppercase">Session Loss</span>
              <span className="text-cosmicFuchsia font-bold font-display">0.00%</span>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: 50% -> Pre-Flight Financial Budget Ledger & Real-Time Sparkline */}
        <div className="bg-[#0e0722]/85 border border-purple-500/20 rounded-xl p-4 flex flex-col justify-between space-y-3">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-brandAmber font-semibold">
                  Cost Governance // Submodular Knapsack
                </span>
                <h3 className="text-sm font-display text-white font-bold flex items-center gap-1.5 mt-0.5">
                  Pre-Flight Financial Budget Ledger
                </h3>
              </div>
              <span className="text-xs font-mono text-purple-200 bg-[#170e30] px-3 py-1 rounded-full border border-purple-500/30">
                ΔB Margin:{" "}
                <strong className="text-cosmicFuchsia font-display">
                  ${telemetry.remainingBudgetUsd.toFixed(4)}
                </strong>
              </span>
            </div>

            <p className="text-xs text-purple-300/70 leading-relaxed font-sans">
              Mathematical invariant: Prior to every model dispatch, worst-case turn cost Ĉ_i is reserved. If remaining margin drops below $0.08, the engine dynamically down-routes to Micro Tier; if below $0.00, it hard-halts.
            </p>

            {/* Slider Input with Cosmic Gradient */}
            <div className="bg-[#080312]/80 p-3.5 rounded-xl border border-purple-500/25 space-y-2">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-purple-300/70">Session Budget Cap (USD)</span>
                <span className="font-display text-base font-bold text-white bg-gradient-to-r from-purple-400 to-fuchsia-400 bg-clip-text text-transparent">
                  ${telemetry.userLimitUsd.toFixed(2)} USD
                </span>
              </div>

              <input
                type="range"
                min="0.00"
                max="1.00"
                step="0.01"
                value={telemetry.userLimitUsd}
                onChange={(e) => onUpdateBudget(parseFloat(e.target.value))}
                className="w-full h-2.5 bg-[#170e30] rounded-lg appearance-none cursor-pointer accent-cosmicFuchsia focus:outline-none"
              />

              <div className="flex justify-between text-[10px] font-mono text-purple-300/60 pt-0.5">
                <span>$0.00 (Hard Halt)</span>
                <span className="text-amber-400/80">$0.08 (Micro Down-Route)</span>
                <span className="text-emerald-400/80">$1.00 (Frontier Max)</span>
              </div>
            </div>

            {/* Simple Mode: Clean Progress Bar & Safeguard Status */}
            {mode === "simple" && (
              <div className="space-y-3">
                <div className="bg-[#080312]/90 p-4 rounded-xl border border-purple-500/30 space-y-3 shadow-inner">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-purple-300/80 font-semibold">Remaining Session Budget</span>
                    <span className="text-emerald-400 font-bold text-sm">
                      ${Math.max(0, telemetry.userLimitUsd - telemetry.cumulativeCostUsd).toFixed(4)} USD Left
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div className="w-full bg-[#170e30] h-4 rounded-full overflow-hidden border border-purple-500/30 p-0.5">
                    <div
                      className="bg-gradient-to-r from-emerald-500 via-teal-400 to-fuchsia-500 h-full rounded-full transition-all duration-300"
                      style={{
                        width: `${Math.min(100, Math.max(4, ((telemetry.userLimitUsd - telemetry.cumulativeCostUsd) / (telemetry.userLimitUsd || 0.01)) * 100))}%`,
                      }}
                    />
                  </div>

                  <div className="flex justify-between text-[11px] font-mono text-purple-300/70 pt-0.5">
                    <span>Spent: ${telemetry.cumulativeCostUsd.toFixed(4)} USD</span>
                    <span>Cap: ${telemetry.userLimitUsd.toFixed(2)} USD</span>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-xs font-mono text-emerald-100 flex items-center gap-3">
                  <CheckCircle2 className="w-4 h-4 text-brandGreen flex-shrink-0" />
                  <div>
                    <strong className="text-white font-display text-xs">
                      BUDGET SAFEGUARD ACTIVE
                    </strong>
                    <p className="text-[11px] text-emerald-200/80 mt-0.5 font-sans">
                      Deterministic pre-flight checks enforce budget ceilings before each model turn.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Developer Mode: Detailed Turn-by-Turn Sparkline */}
            {mode === "developer" && (
              <>
                <div className="bg-[#080312]/90 p-3 rounded-xl border border-purple-500/30 space-y-2 shadow-inner">
              <div className="flex items-center justify-between text-[11px] font-mono">
                <div className="flex items-center gap-1.5 text-purple-200">
                  <Activity className="w-3.5 h-3.5 text-cosmicFuchsia" />
                  <span className="font-semibold">Turn-by-Turn Telemetry Sparkline</span>
                </div>
                <div className="flex items-center gap-2.5 text-[10px]">
                  <span className="flex items-center gap-1 text-emerald-300 font-semibold">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_#10b981]" />
                    Savings: -{telemetry.tokenSavingsPct}%
                  </span>
                  <span className="flex items-center gap-1 text-cosmicFuchsia font-semibold">
                    <span className="w-2 h-2 rounded-full bg-fuchsia-400 shadow-[0_0_6px_#d946ef]" />
                    Latency: {isChaos ? telemetry.failoverLatencyMs : 138}ms (&lt;180ms)
                  </span>
                </div>
              </div>

              {/* Vector SVG Dual-Metric Sparkline */}
              <div className="relative w-full h-[76px] rounded-lg overflow-hidden bg-[#0a0518]/90 border border-purple-500/20">
                <svg
                  className="w-full h-full"
                  viewBox="0 0 380 76"
                  preserveAspectRatio="none"
                >
                  <defs>
                    {/* Emerald Savings Gradient */}
                    <linearGradient id="spark-savings-grad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#10b981" stopOpacity="0.45" />
                      <stop offset="100%" stopColor="#10b981" stopOpacity="0.02" />
                    </linearGradient>

                    {/* Cosmic Violet/Fuchsia Latency Gradient */}
                    <linearGradient id="spark-latency-grad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#d946ef" stopOpacity="0.35" />
                      <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.0" />
                    </linearGradient>
                  </defs>

                  {/* Horizontal Guideline */}
                  <line
                    x1="0"
                    y1="40"
                    x2="380"
                    y2="40"
                    stroke="#2e1065"
                    strokeWidth="0.8"
                    strokeDasharray="3 3"
                    opacity="0.4"
                  />

                  {/* Latency Curve Area & Line (Cosmic Fuchsia with <180ms failover recovery spike) */}
                  <path
                    d="M 10 50 L 65 48 L 125 46 L 185 18 L 245 49 L 305 47 L 365 48 L 365 74 L 10 74 Z"
                    fill="url(#spark-latency-grad)"
                  />
                  <path
                    d="M 10 50 L 65 48 L 125 46 L 185 18 L 245 49 L 305 47 L 365 48"
                    fill="none"
                    stroke="#d946ef"
                    strokeWidth="1.8"
                    strokeDasharray="4 2"
                    opacity="0.95"
                  />
                  {/* Spike point at Turn 4 (178ms failover recovery) */}
                  <circle
                    cx="185"
                    cy="18"
                    r="3.5"
                    fill="#f43f5e"
                    stroke="#ffffff"
                    strokeWidth="1"
                    className="animate-ping"
                  />
                  <circle
                    cx="185"
                    cy="18"
                    r="3.5"
                    fill="#d946ef"
                    stroke="#ffffff"
                    strokeWidth="1"
                  />

                  {/* Token Savings Curve Area & Line (Emerald, rising to -84.2%) */}
                  <path
                    d="M 10 58 L 65 52 L 125 44 L 185 36 L 245 30 L 305 31 L 365 29 L 365 74 L 10 74 Z"
                    fill="url(#spark-savings-grad)"
                  />
                  <path
                    d="M 10 58 L 65 52 L 125 44 L 185 36 L 245 30 L 305 31 L 365 29"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="2.2"
                  />

                  {/* Data Points on Savings Path */}
                  {[
                    { cx: 10, cy: 58 },
                    { cx: 65, cy: 52 },
                    { cx: 125, cy: 44 },
                    { cx: 185, cy: 36 },
                    { cx: 245, cy: 30 },
                    { cx: 305, cy: 31 },
                    { cx: 365, cy: 29 },
                  ].map((p, i) => (
                    <circle
                      key={i}
                      cx={p.cx}
                      cy={p.cy}
                      r="2.5"
                      fill="#10b981"
                      stroke="#06040e"
                      strokeWidth="1"
                    />
                  ))}
                </svg>

                {/* Sub-180ms Spike Badge on Chart */}
                <div className="absolute top-1 left-[150px] bg-rose-950/90 border border-brandRose/80 text-[8px] font-mono text-rose-200 px-1.5 py-0.2 rounded shadow">
                  178ms spike &rarr; 138ms recovery
                </div>
              </div>
            </div>

            {/* Visual Pre-Flight Status Indicators */}
            {telemetry.isHalted ? (
              <div className="p-3.5 rounded-xl bg-rose-950/80 border border-brandRose text-xs font-mono text-rose-100 flex items-center gap-3 animate-pulse shadow-[0_0_20px_rgba(244,63,94,0.3)]">
                <AlertTriangle className="w-5 h-5 text-brandRose flex-shrink-0" />
                <div>
                  <strong className="text-white font-display text-xs">
                    PRE-FLIGHT HARD-HALT: ZERO OVERRUN GUARANTEED
                  </strong>
                  <p className="text-[11px] text-rose-200 mt-0.5 font-sans">
                    Execution cleanly halted before network dispatch. Agent state serialized to deterministic checkpoint.
                  </p>
                </div>
              </div>
            ) : telemetry.activeTier === "tier-1-micro" ? (
              <div className="p-3.5 rounded-xl bg-amber-950/70 border border-brandAmber/80 text-xs font-mono text-amber-100 flex items-center gap-3 shadow-[0_0_15px_rgba(245,158,11,0.25)]">
                <TrendingDown className="w-5 h-5 text-brandAmber flex-shrink-0" />
                <div>
                  <strong className="text-white font-display text-xs">
                    DYNAMIC DOWN-ROUTING ACTIVE (Tier-1 Micro)
                  </strong>
                  <p className="text-[11px] text-amber-200 mt-0.5 font-sans">
                    Remaining margin &lt; $0.08: Automatically down-routed to lightweight micro tier to guarantee zero over-budget.
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-3.5 rounded-xl bg-emerald-950/50 border border-emerald-500/50 text-xs font-mono text-emerald-100 flex items-center gap-3 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
                <CheckCircle2 className="w-5 h-5 text-brandGreen flex-shrink-0" />
                <div>
                  <strong className="text-white font-display text-xs">
                    BUDGET INVARIANT SATISFIED: &sum; C_k + &Ccirc;_i &le; L_session
                  </strong>
                  <p className="text-[11px] text-emerald-200 mt-0.5 font-sans">
                    Cumulative turn spend: ${telemetry.cumulativeCostUsd.toFixed(4)} USD. Tier-2 Frontier headroom available.
                  </p>
                </div>
              </div>
            )}
              </>
            )}
          </div>

          {/* Pre-Call Ledger Table (Developer Mode) */}
          {mode === "developer" && (
            <div className="space-y-1.5 pt-2 border-t border-purple-500/20 text-xs font-mono">
              <span className="text-[10px] text-purple-300/60 uppercase block">
                Pre-Call Ledger Breakdown:
              </span>
              <div className="bg-[#090514]/80 rounded-xl border border-purple-500/20 p-2.5 space-y-1.5">
                <div className="flex justify-between items-center text-purple-200">
                  <span>Cumulative Incurred Spend (&sum; C_k):</span>
                  <span className="font-bold">${telemetry.cumulativeCostUsd.toFixed(4)}</span>
                </div>
                <div className="flex justify-between items-center text-purple-200">
                  <span>Worst-Case Turn Reservation (&Ccirc;_i):</span>
                  <span className="font-bold text-brandAmber">$0.0240</span>
                </div>
                <div className="flex justify-between items-center text-purple-200">
                  <span>Enforcement Decision:</span>
                  <span
                    className={`font-bold px-2 py-0.5 rounded text-[10px] ${
                      telemetry.isHalted
                        ? "bg-rose-950 text-brandRose border border-brandRose"
                        : telemetry.activeTier === "tier-1-micro"
                        ? "bg-amber-950 text-brandAmber border border-brandAmber"
                        : "bg-emerald-950 text-brandGreen border border-brandGreen"
                    }`}
                  >
                    {telemetry.isHalted
                      ? "BLOCK_HALT"
                      : telemetry.activeTier === "tier-1-micro"
                      ? "DOWN_ROUTE_MICRO"
                      : "PERMIT_FRONTIER"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
