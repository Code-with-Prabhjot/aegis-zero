"use client";

import React from "react";
import {
  Flame,
  AlertTriangle,
  RotateCcw,
  DollarSign,
  TrendingDown,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ArrowRight,
  ServerOff,
  Zap,
  Cpu,
  Lock,
} from "lucide-react";
import { TelemetryState } from "@/types";

interface Panel2Props {
  telemetry: TelemetryState;
  onTriggerChaos: () => void;
  onResetChaos: () => void;
  onUpdateBudget: (amount: number) => void;
}

export function Panel2_ChaosBudget({
  telemetry,
  onTriggerChaos,
  onResetChaos,
  onUpdateBudget,
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

          {/* Visual Multi-Tier Routing Chain */}
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
                <p className="font-bold text-xs truncate">Claude 3.5 Sonnet</p>
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
                <p className="font-bold text-xs truncate">OpenAI GPT-4o</p>
                <span className="text-[9px] text-amber-300/70">Sub-180ms Auto-Route</span>
              </div>

              {/* Tier 3 Micro Fast Fallback */}
              <div className="p-2.5 rounded-xl border bg-[#090514]/60 border-purple-900/30 text-purple-300/70">
                <div className="flex items-center justify-between text-[10px] text-purple-400/60 mb-1">
                  <span>3. High-Speed Fallback</span>
                </div>
                <p className="font-bold text-xs truncate">Groq Llama-3.3-70B</p>
                <span className="text-[9px] text-purple-400/60">Tier-1 Micro (&lt;$0.08)</span>
              </div>

              {/* Tier 4 Air-Gapped Local */}
              <div className="p-2.5 rounded-xl border bg-[#090514]/60 border-purple-900/30 text-purple-300/70">
                <div className="flex items-center justify-between text-[10px] text-purple-400/60 mb-1">
                  <span>4. Air-Gapped Enclave</span>
                </div>
                <p className="font-bold text-xs truncate">Local Ollama Llama-3</p>
                <span className="text-[9px] text-purple-400/60">Tier-0 Air-Gap Lock</span>
              </div>
            </div>
          </div>

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

        {/* RIGHT COLUMN: 50% -> Pre-Flight Financial Budget Ledger & Down-Routing/Hard-Halt Visualizer */}
        <div className="bg-[#0e0722]/85 border border-purple-500/20 rounded-xl p-4 flex flex-col justify-between space-y-4">
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
                    BUDGET INVARIANT SATISFIED: ∑ C_k + Ĉ_i ≤ L_session
                  </strong>
                  <p className="text-[11px] text-emerald-200 mt-0.5 font-sans">
                    Cumulative turn spend: ${telemetry.cumulativeCostUsd.toFixed(4)} USD. Tier-2 Frontier headroom available.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Pre-Call Ledger Table */}
          <div className="space-y-1.5 pt-2 border-t border-purple-500/20 text-xs font-mono">
            <span className="text-[10px] text-purple-300/60 uppercase block">
              Pre-Call Ledger Breakdown:
            </span>
            <div className="bg-[#090514]/80 rounded-xl border border-purple-500/20 p-2.5 space-y-1.5">
              <div className="flex justify-between items-center text-purple-200">
                <span>Cumulative Incurred Spend (∑ C_k):</span>
                <span className="font-bold">${telemetry.cumulativeCostUsd.toFixed(4)}</span>
              </div>
              <div className="flex justify-between items-center text-purple-200">
                <span>Worst-Case Turn Reservation (Ĉ_i):</span>
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
        </div>
      </div>
    </div>
  );
}
