"use client";

import React from "react";
import {
  Flame,
  AlertTriangle,
  RotateCcw,
  Sliders,
  DollarSign,
  TrendingDown,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ArrowRight,
  ServerOff,
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
  const isChaos = telemetry.gatewayStatus === "CHAOS_INJECTED" || telemetry.circuitBreakerTripped;

  return (
    <div className="flex flex-col h-full bg-surface border border-borderDark rounded-lg overflow-hidden shadow-lg">
      {/* Panel Header */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-surfaceHover/80 border-b border-borderDark">
        <div className="flex items-center gap-2">
          <Flame className="w-4 h-4 text-brandRose" />
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-100">
            Panel 2 // Chaos Failover Simulator &amp; Budget Controls
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
              isChaos
                ? "bg-red-950/80 border-brandRose/80 text-brandRose animate-pulse"
                : "bg-emerald-950/70 border-brandGreen/60 text-brandGreen"
            }`}
          >
            CIRCUIT-BREAKER: {isChaos ? "OPEN (CHAOS)" : "CLOSED (HEALTHY)"}
          </span>
        </div>
      </div>

      {/* Main Container */}
      <div className="p-4 space-y-4 flex-1 flex flex-col justify-between bg-[#080c14]">
        {/* SECTION A: 1-Click Judge Chaos Outage Trigger */}
        <div className="bg-surface/80 border border-borderDark rounded-lg p-3.5 relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                Resilience Engine // Bifrost AI Gateway
              </span>
              <h3 className="text-sm font-mono font-bold text-slate-100 flex items-center gap-1.5">
                Judge 1-Click Chaos Simulation
              </h3>
            </div>
            {isChaos && (
              <span className="flex items-center gap-1 text-[11px] font-mono text-brandRose font-bold animate-pulse">
                <AlertTriangle className="w-3.5 h-3.5 text-brandRose" />
                OUTAGE ACTIVE
              </span>
            )}
          </div>

          <p className="text-xs text-slate-400 mb-3 leading-relaxed">
            Click to simulate a real-time HTTP 429 Rate-Limit / Provider Outage on the primary frontier model.
            Observe automated zero-session-loss circuit breaker trip to GPT-4o in sub-180ms.
          </p>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={onTriggerChaos}
              disabled={isChaos}
              className={`flex-1 min-w-[200px] flex items-center justify-center gap-2 px-4 py-2.5 rounded font-mono text-xs font-bold transition-all shadow-md active:scale-95 ${
                isChaos
                  ? "bg-red-950/40 border border-red-800 text-red-500 cursor-not-allowed opacity-60"
                  : "bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 text-white shadow-[0_0_15px_rgba(244,63,94,0.4)] border border-rose-400 cursor-pointer"
              }`}
            >
              <ServerOff className="w-4 h-4" />
              <span>[SIMULATE HTTP 429 OUTAGE]</span>
            </button>

            <button
              onClick={onResetChaos}
              disabled={!isChaos}
              className={`flex items-center justify-center gap-1.5 px-3 py-2.5 rounded font-mono text-xs font-semibold transition-all border ${
                isChaos
                  ? "bg-surfaceHover border-brandGreen/60 text-brandGreen hover:bg-emerald-950/40 cursor-pointer shadow-sm active:scale-95"
                  : "bg-surfaceHover/40 border-slate-700 text-slate-600 cursor-not-allowed"
              }`}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>RESTORE PRIMARY MODEL</span>
            </button>
          </div>

          {/* Sub-180ms Failover HUD Banner */}
          {isChaos && (
            <div className="mt-3 p-2.5 rounded bg-red-950/50 border border-brandRose/70 flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2 text-rose-200">
                <Clock className="w-4 h-4 text-brandRose animate-spin" />
                <span>
                  FAILOVER COMPLETE: <strong className="text-white">{telemetry.failoverLatencyMs}ms</strong>
                </span>
                <span className="text-brandGreen text-[11px]">(0 Session Loss)</span>
              </div>
              <span className="text-slate-300 text-[11px]">Route: GPT-4o Secondary</span>
            </div>
          )}

          {/* Fallback Chain Breadcrumbs */}
          <div className="mt-3 pt-2 border-t border-borderDark/60 flex flex-wrap items-center gap-1.5 text-[10px] font-mono">
            <span className="text-slate-500">Routing Chain:</span>
            <span
              className={`px-1.5 py-0.5 rounded ${
                !isChaos
                  ? "bg-cyan-950 border border-cyan-500/80 text-cyan-300 font-bold"
                  : "bg-slate-800 text-slate-500 line-through"
              }`}
            >
              1. Claude 3.5 Sonnet
            </span>
            <ArrowRight className="w-3 h-3 text-slate-600" />
            <span
              className={`px-1.5 py-0.5 rounded ${
                isChaos
                  ? "bg-amber-950 border border-amber-500/80 text-amber-300 font-bold shadow-[0_0_8px_#f59e0b]"
                  : "bg-slate-800 text-slate-500"
              }`}
            >
              2. OpenAI GPT-4o
            </span>
            <ArrowRight className="w-3 h-3 text-slate-600" />
            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">
              3. Groq Llama-3.3-70B
            </span>
            <ArrowRight className="w-3 h-3 text-slate-600" />
            <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">
              4. Local Ollama
            </span>
          </div>
        </div>

        {/* SECTION B: Interactive USD Budget Slider & Pre-Call Enforcement */}
        <div className="bg-surface/80 border border-borderDark rounded-lg p-3.5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <DollarSign className="w-4 h-4 text-brandAmber" />
              <span className="text-xs font-mono font-bold text-slate-100">
                Pre-Flight Budget Enforcement Ledger
              </span>
            </div>
            <span className="text-[11px] font-mono text-brandCyan">
              Remaining Margin ΔB: ${telemetry.remainingBudgetUsd.toFixed(4)}
            </span>
          </div>

          {/* Slider input */}
          <div>
            <div className="flex justify-between text-xs font-mono text-slate-400 mb-1">
              <span>Session Budget Cap (USD)</span>
              <span className="text-white font-bold text-sm">
                ${telemetry.userLimitUsd.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0.00"
              max="1.00"
              step="0.01"
              value={telemetry.userLimitUsd}
              onChange={(e) => onUpdateBudget(parseFloat(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-brandCyan focus:outline-none"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500 mt-1">
              <span>$0.00 (Hard Halt)</span>
              <span>$0.08 (Micro Down-Route)</span>
              <span>$1.00 Max</span>
            </div>
          </div>

          {/* Visual Pre-Flight Status Indicators */}
          {telemetry.isHalted ? (
            <div className="p-2.5 rounded bg-red-950/80 border border-brandRose text-xs font-mono text-rose-200 flex items-center gap-2 animate-bounce">
              <AlertTriangle className="w-4 h-4 text-brandRose flex-shrink-0" />
              <div>
                <strong>PRE-FLIGHT HARD-HALT: ZERO OVERRUN GUARANTEED</strong>
                <p className="text-[10px] text-rose-300">
                  Execution cleanly halted prior to network dispatch. Agent state serialized to checkpoint.
                </p>
              </div>
            </div>
          ) : telemetry.activeTier === "tier-1-micro" ? (
            <div className="p-2.5 rounded bg-amber-950/70 border border-brandAmber/80 text-xs font-mono text-amber-200 flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-brandAmber flex-shrink-0" />
              <div>
                <strong>DYNAMIC DOWN-ROUTING ACTIVE</strong>
                <p className="text-[10px] text-amber-300">
                  Remaining margin &lt; $0.08: Automatically down-routed to Tier-1 Micro to guarantee zero over-budget.
                </p>
              </div>
            </div>
          ) : (
            <div className="p-2.5 rounded bg-emerald-950/50 border border-emerald-500/50 text-xs font-mono text-emerald-200 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-brandGreen flex-shrink-0" />
              <div>
                <span>BUDGET INVARIANT SATISFIED: ∑ C_k + Ĉ_i ≤ L_session</span>
                <p className="text-[10px] text-emerald-400">
                  Cumulative turn cost: ${telemetry.cumulativeCostUsd.toFixed(4)} USD. Tier-2 Frontier headroom available.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
