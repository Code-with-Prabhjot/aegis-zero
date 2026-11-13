"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ShieldCheck,
  Zap,
  Cpu,
  RefreshCw,
  Lock,
  Radio,
  FileCode2,
  ArrowLeft,
} from "lucide-react";
import { TelemetryState } from "@/types";

interface HeaderProps {
  telemetry: TelemetryState;
  isConnected: boolean;
  onLoadDemo: () => void;
  onToggleTaint: () => void;
}

export function Header({
  telemetry,
  isConnected,
  onLoadDemo,
  onToggleTaint,
}: HeaderProps) {
  const getStatusBadge = () => {
    if (telemetry.gatewayStatus === "CHAOS_INJECTED") {
      return (
        <div className="flex items-center gap-1.5 px-3 py-1 bg-red-950/80 border border-brandRose/70 rounded-full text-brandRose text-xs font-mono font-semibold animate-pulse">
          <span className="w-2 h-2 rounded-full bg-brandRose shadow-[0_0_8px_#f43f5e]" />
          CHAOS (HTTP 429) &rarr; FAILOVER: {telemetry.activeModel}
        </div>
      );
    }
    if (telemetry.circuitBreakerTripped) {
      return (
        <div className="flex items-center gap-1.5 px-3 py-1 bg-amber-950/80 border border-brandAmber/70 rounded-full text-brandAmber text-xs font-mono font-semibold">
          <span className="w-2 h-2 rounded-full bg-brandAmber shadow-[0_0_8px_#f59e0b]" />
          FAILOVER: {telemetry.activeModel} ({telemetry.failoverLatencyMs}ms)
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-950/60 border border-brandGreen/60 rounded-full text-brandGreen text-xs font-mono font-semibold">
        <span className="w-2 h-2 rounded-full bg-brandGreen shadow-[0_0_8px_#10b981]" />
        ONLINE (PRIMARY: {telemetry.activeModel.split("-").slice(0, 3).join("-")})
      </div>
    );
  };

  const getTierBadge = () => {
    switch (telemetry.activeTier) {
      case "tier-0-local":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-purple-950/80 border border-purple-500/60 text-purple-300 text-xs font-mono">
            <Lock className="w-3.5 h-3.5 text-purple-400" />
            Tier-0 Local Enclave
          </span>
        );
      case "tier-1-micro":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-amber-950/80 border border-amber-500/60 text-amber-300 text-xs font-mono">
            <Cpu className="w-3.5 h-3.5 text-amber-400" />
            Tier-1 Micro
          </span>
        );
      case "tier-2-frontier":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-cyan-950/80 border border-cyan-500/60 text-cyan-300 text-xs font-mono">
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            Tier-2 Frontier
          </span>
        );
    }
  };

  return (
    <header className="w-full border-b border-borderDark/80 bg-surface/90 backdrop-blur-md px-4 py-3 sticky top-0 z-50">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Brand & Mission Tag */}
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-surfaceHover/90 border border-borderDark hover:border-brandCyan/60 text-slate-300 hover:text-brandCyan text-xs font-mono transition-all shadow-sm active:scale-95 group"
            title="Return to Aegis-0 Overview & Landing Page"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-brandCyan group-hover:-translate-x-0.5 transition-transform" />
            <span className="hidden sm:inline">Back to Overview</span>
          </Link>
          <div className="relative flex items-center justify-center w-9 h-9 rounded bg-brandCyan/10 border border-brandCyan/40 shadow-[0_0_12px_rgba(6,182,212,0.25)]">
            <Radio className="w-5 h-5 text-brandCyan animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm md:text-base font-bold font-mono tracking-wider text-slate-100">
                AEGIS-0
              </span>
              <span className="text-xs font-mono text-brandCyan px-1.5 py-0.5 rounded bg-brandCyan/15 border border-brandCyan/30">
                MISSION CONTROL WORKBENCH
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono tracking-tight hidden sm:block">
              Zero-Trust Token-Optimal Autonomous Coding &amp; Live-Verification Engine
            </p>
          </div>
        </div>

        {/* Live Status Indicators */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Gateway Status */}
          {getStatusBadge()}

          {/* Token Optimization Badge */}
          <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-950/50 border border-emerald-500/40 rounded-full text-brandGreen text-xs font-mono font-medium">
            <Zap className="w-3.5 h-3.5 text-brandGreen" />
            <span>-{telemetry.tokenSavingsPct}% TOKENS SAVED</span>
          </div>

          {/* Air Gap Lock Badge */}
          {telemetry.airGapLock ? (
            <div className="flex items-center gap-1.5 px-3 py-1 bg-purple-950/80 border border-purple-500/80 rounded-full text-purple-300 text-xs font-mono font-semibold animate-pulse shadow-[0_0_10px_rgba(168,85,247,0.3)]">
              <ShieldAlert className="w-3.5 h-3.5 text-purple-400" />
              <span>AIR-GAP LOCKED: ZERO WAN</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-1 bg-slate-800/80 border border-slate-700 rounded-full text-slate-300 text-xs font-mono">
              <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
              <span>WAN ENABLED</span>
            </div>
          )}

          {/* Active Model Tier */}
          {getTierBadge()}

          {/* Backend Status indicator */}
          <div
            className={`flex items-center gap-1 px-2 py-1 rounded text-[10px] font-mono border ${
              isConnected
                ? "text-emerald-400 border-emerald-800/50 bg-emerald-950/20"
                : "text-slate-400 border-slate-700/50 bg-slate-900/40"
            }`}
            title={isConnected ? "WebSocket Connected to FastApi" : "Standalone High-Fidelity Mode"}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isConnected ? "bg-emerald-400" : "bg-slate-500"
              }`}
            />
            {isConnected ? "WS: LIVE" : "STANDALONE"}
          </div>
        </div>

        {/* Quick Launch Judge Demo Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={onLoadDemo}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-surfaceHover border border-borderDark hover:border-brandCyan/60 text-slate-200 hover:text-brandCyan text-xs font-mono transition-all shadow-sm active:scale-95"
            title="Reload repository AST benchmark scenario"
          >
            <FileCode2 className="w-3.5 h-3.5 text-brandCyan" />
            <span className="hidden md:inline">Load Demo Refactor Task</span>
            <span className="md:hidden">Demo</span>
          </button>

          <button
            onClick={onToggleTaint}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded border text-xs font-mono transition-all shadow-sm active:scale-95 ${
              telemetry.airGapLock
                ? "bg-purple-900/60 border-purple-500 text-purple-200 shadow-[0_0_8px_rgba(168,85,247,0.4)]"
                : "bg-surfaceHover border-borderDark hover:border-purple-400 text-slate-200 hover:text-purple-300"
            }`}
            title="Simulate proprietary repo taint triggering air-gap lock"
          >
            <Lock className="w-3.5 h-3.5 text-purple-400" />
            <span className="hidden md:inline">
              {telemetry.airGapLock ? "Release Enclave Lock" : "Inject Confidential Repo Taint"}
            </span>
            <span className="md:hidden">Taint</span>
          </button>
        </div>
      </div>
    </header>
  );
}
