"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ShieldCheck,
  Zap,
  ArrowLeft,
  FileCode2,
  Lock,
  Layers,
  Wrench,
  Sparkles,
} from "lucide-react";
import { TelemetryState } from "@/types";

interface HeaderProps {
  telemetry: TelemetryState;
  isConnected: boolean;
  onLoadDemo: () => void;
  onToggleTaint: () => void;
  activeStage?: 1 | 2 | 3;
  onSelectStage?: (stage: 1 | 2 | 3) => void;
  mode: "simple" | "developer";
  onToggleMode: (mode: "simple" | "developer") => void;
}

export function Header({
  telemetry,
  isConnected,
  onLoadDemo,
  onToggleTaint,
  activeStage = 1,
  onSelectStage,
  mode = "simple",
  onToggleMode,
}: HeaderProps) {
  const isChaos =
    telemetry.gatewayStatus === "CHAOS_INJECTED" || telemetry.circuitBreakerTripped;

  const staleCount = telemetry.claims.filter((c) => c.is_stale).length;
  const isQuarantined =
    telemetry.quarantinedAction?.is_quarantined &&
    !telemetry.quarantinedAction?.is_approved;

  const getTierLabel = () => {
    switch (telemetry.activeTier) {
      case "tier-0-local":
        return "Tier-0 Local";
      case "tier-1-micro":
        return "Tier-1 Micro";
      case "tier-2-frontier":
      default:
        return "Tier-2 Frontier";
    }
  };

  return (
    <header className="w-full max-w-[1920px] mx-auto px-2 sm:px-3 md:px-4 py-2 sticky top-0 z-50">
      <div className="rounded-full bg-[#0d081c]/90 border border-purple-500/25 backdrop-blur-xl shadow-[0_10px_35px_-10px_rgba(139,92,246,0.35)] px-3 py-1.5 flex items-center justify-between gap-2 overflow-x-auto no-scrollbar whitespace-nowrap">
        {/* LEFT: Brand Mark + Overview Link + Status Badges */}
        <div className="flex items-center gap-2 flex-shrink-0 whitespace-nowrap">
          <Link
            href="/"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#180f33]/80 border border-purple-500/30 hover:border-cosmicFuchsia/60 text-purple-200 hover:text-white text-xs font-mono transition-all shadow-sm active:scale-95 group"
            title="Return to AEGIS-0 Landing Page"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-cosmicFuchsia group-hover:-translate-x-0.5 transition-transform" />
            <span className="hidden sm:inline">Overview</span>
          </Link>

          {/* Brand Mark */}
          <div className="flex items-center gap-1.5 pl-1 pr-2 border-r border-purple-500/20">
            <div className="w-2 h-2 rounded-full bg-cosmicFuchsia shadow-[0_0_8px_#d946ef] animate-pulse" />
            <span className="font-display text-xs md:text-sm tracking-widest text-white font-bold">
              AEGIS <span className="text-cosmicFuchsia">0</span>
            </span>
          </div>

          {/* Clean Status Indicators */}
          <div className="flex items-center gap-1 text-[10px] font-mono">
            {/* Gateway Pill */}
            {isChaos ? (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-950/80 border border-brandRose/70 text-brandRose font-semibold animate-pulse shadow-[0_0_8px_rgba(244,63,94,0.3)]">
                <span className="w-1.5 h-1.5 rounded-full bg-brandRose" />
                429 CHAOS
              </span>
            ) : (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-950/70 border border-brandGreen/60 text-brandGreen font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-brandGreen shadow-[0_0_6px_#10b981]" />
                ONLINE
              </span>
            )}

            {/* Token Savings Pill */}
            <span className="hidden md:flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-950/50 border border-emerald-500/40 text-brandGreen font-medium">
              <Zap className="w-3 h-3 text-brandGreen" />
              -{telemetry.tokenSavingsPct}% TOKENS
            </span>

            {/* Developer-Only Badges */}
            {mode === "developer" && (
              <>
                {telemetry.airGapLock ? (
                  <span className="hidden xl:flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-950/80 border border-purple-500/80 text-purple-200 font-semibold animate-pulse">
                    <ShieldAlert className="w-3 h-3 text-purple-400" />
                    AIR-GAP
                  </span>
                ) : (
                  <span className="hidden xl:flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-900/60 border border-purple-500/20 text-purple-300/80">
                    <ShieldCheck className="w-3 h-3 text-purple-400/80" />
                    WAN
                  </span>
                )}

                <span className="hidden 2xl:flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-950/50 border border-purple-500/30 text-purple-300">
                  {getTierLabel()}
                </span>

                <span
                  className={`hidden lg:flex items-center gap-1 px-2 py-0.5 rounded-full border ${
                    isConnected
                      ? "text-emerald-400 border-emerald-700/50 bg-emerald-950/30"
                      : "text-purple-300/60 border-purple-800/40 bg-purple-950/20"
                  }`}
                  title={isConnected ? "WebSocket Connected" : "Standalone High-Fidelity Fallback"}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      isConnected ? "bg-emerald-400" : "bg-purple-400/60"
                    }`}
                  />
                  {isConnected ? "WS: LIVE" : "STANDALONE"}
                </span>
              </>
            )}
          </div>
        </div>

        {/* CENTER: 3-Stage Workspace Switcher Pills (Single-Line, Compact, Whitespace-Nowrap) */}
        <div className="flex items-center gap-1 bg-[#080414]/90 p-0.5 rounded-full border border-purple-500/20 flex-shrink-0 whitespace-nowrap">
          {/* Stage 1: Context */}
          <button
            onClick={() => onSelectStage?.(1)}
            className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-full text-xs font-mono transition-all duration-200 whitespace-nowrap ${
              activeStage === 1
                ? "bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white font-bold shadow-[0_0_14px_rgba(217,70,239,0.4)] border border-fuchsia-400/40"
                : "text-purple-300/70 hover:text-white hover:bg-purple-900/30 border border-transparent"
            }`}
            title="Stage 01: Submodular AST Context Pruner"
          >
            <span className="font-semibold whitespace-nowrap">01 · Context</span>
            <span
              className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold whitespace-nowrap ${
                activeStage === 1
                  ? "bg-black/30 text-emerald-300 border border-emerald-400/40"
                  : "bg-emerald-950/60 text-brandGreen border border-brandGreen/40"
              }`}
            >
              {telemetry.tokenSavingsPct}% Saved
            </span>
          </button>

          {/* Stage 2: Resilience */}
          <button
            onClick={() => onSelectStage?.(2)}
            className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-full text-xs font-mono transition-all duration-200 whitespace-nowrap ${
              activeStage === 2
                ? "bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white font-bold shadow-[0_0_14px_rgba(217,70,239,0.4)] border border-fuchsia-400/40"
                : "text-purple-300/70 hover:text-white hover:bg-purple-900/30 border border-transparent"
            }`}
            title="Stage 02: Bifrost Gateway Resilience & Budget Controls"
          >
            <span className="font-semibold whitespace-nowrap">02 · Resilience</span>
            <span
              className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold whitespace-nowrap ${
                isChaos
                  ? "bg-rose-950/90 text-brandRose border border-brandRose/60 animate-pulse shadow-[0_0_8px_rgba(244,63,94,0.3)]"
                  : activeStage === 2
                  ? "bg-black/30 text-emerald-300 border border-emerald-400/40"
                  : "bg-emerald-950/60 text-brandGreen border border-brandGreen/40"
              }`}
            >
              {isChaos ? "FAILOVER" : "HEALTHY"}
            </span>
          </button>

          {/* Stage 3: Verify & Gate */}
          <button
            onClick={() => onSelectStage?.(3)}
            className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-full text-xs font-mono transition-all duration-200 whitespace-nowrap ${
              activeStage === 3
                ? "bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white font-bold shadow-[0_0_14px_rgba(217,70,239,0.4)] border border-fuchsia-400/40"
                : "text-purple-300/70 hover:text-white hover:bg-purple-900/30 border border-transparent"
            }`}
            title="Stage 03: Tavily Verification & Human-in-the-Loop Action Gate"
          >
            <span className="font-semibold whitespace-nowrap">03 · Verify &amp; Gate</span>
            <span
              className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold whitespace-nowrap ${
                isQuarantined
                  ? "bg-rose-950/90 text-brandRose border border-brandRose/60 animate-pulse shadow-[0_0_8px_rgba(244,63,94,0.3)]"
                  : staleCount > 0
                  ? "bg-amber-950/90 text-amber-300 border border-amber-500/60"
                  : activeStage === 3
                  ? "bg-black/30 text-emerald-300 border border-emerald-400/40"
                  : "bg-emerald-950/60 text-brandGreen border border-brandGreen/40"
              }`}
            >
              {isQuarantined
                ? "QUARANTINE"
                : staleCount > 0
                ? `${staleCount} STALE`
                : "VERIFIED"}
            </span>
          </button>
        </div>

        {/* RIGHT: Mode Switcher + Action Pills */}
        <div className="flex items-center gap-2 flex-shrink-0 whitespace-nowrap">
          {/* Segmented Mode Toggle: Simple (Default) | Developer */}
          <div className="flex items-center bg-[#140a2b] p-0.5 rounded-full border border-purple-500/35 text-[11px] font-mono shadow-inner whitespace-nowrap">
            <button
              type="button"
              onClick={() => onToggleMode("simple")}
              className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full transition-all duration-150 ${
                mode === "simple"
                  ? "bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white font-bold shadow-[0_0_10px_rgba(217,70,239,0.45)]"
                  : "text-purple-300/60 hover:text-purple-100"
              }`}
              title="Simple Mode: Clean, spacious, presentation-ready dashboard"
            >
              <Sparkles className="w-3 h-3" />
              <span>Simple</span>
            </button>
            <button
              type="button"
              onClick={() => onToggleMode("developer")}
              className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full transition-all duration-150 ${
                mode === "developer"
                  ? "bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white font-bold shadow-[0_0_10px_rgba(217,70,239,0.45)]"
                  : "text-purple-300/60 hover:text-purple-100"
              }`}
              title="Developer Mode: Full engineering telemetry, formulas, and red-team tools"
            >
              <Wrench className="w-3 h-3" />
              <span>Developer</span>
            </button>
          </div>

          {/* Quick Demo Task Pill */}
          <button
            onClick={onLoadDemo}
            className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#170e30]/80 hover:bg-[#25154d] border border-purple-500/30 hover:border-cosmicFuchsia/60 text-purple-200 hover:text-white text-xs font-mono transition-all shadow-sm active:scale-95"
            title="Reload repository AST benchmark scenario"
          >
            <FileCode2 className="w-3 h-3 text-cosmicFuchsia" />
            <span className="hidden lg:inline text-[11px]">Demo</span>
          </button>

          {/* Taint Repo Toggle (In Developer Mode or when locked) */}
          {(mode === "developer" || telemetry.airGapLock) && (
            <button
              onClick={onToggleTaint}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-full border text-xs font-mono transition-all shadow-sm active:scale-95 ${
                telemetry.airGapLock
                  ? "bg-purple-900/60 border-cosmicFuchsia text-purple-100 shadow-[0_0_12px_rgba(217,70,239,0.4)]"
                  : "bg-[#170e30]/80 hover:bg-[#25154d] border-purple-500/30 hover:border-purple-400 text-purple-200 hover:text-white"
              }`}
              title="Simulate proprietary repo taint triggering air-gap lock"
            >
              <Lock className="w-3 h-3 text-purple-300" />
              <span className="hidden xl:inline text-[11px]">
                {telemetry.airGapLock ? "Locked" : "Taint"}
              </span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
