"use client";

import React from "react";
import { Header } from "@/components/Header";
import { Panel1_ASTGraph } from "@/components/Panel1_ASTGraph";
import { Panel2_ChaosBudget } from "@/components/Panel2_ChaosBudget";
import { Panel3_TavilyScorecard } from "@/components/Panel3_TavilyScorecard";
import { Panel4_MonacoVoiceGate } from "@/components/Panel4_MonacoVoiceGate";
import { useOrchestrator } from "@/hooks/useOrchestrator";
import { Bell, Info } from "lucide-react";

export default function MissionControlPage() {
  const {
    telemetry,
    isConnected,
    failoverToast,
    setFailoverToast,
    triggerChaosOutage,
    resetChaos,
    updateBudgetCap,
    approveAction,
    applyFreshPatch,
    loadDemoRefactor,
    injectConfidentialTaint,
  } = useOrchestrator();

  return (
    <main className="min-h-screen flex flex-col bg-background text-slate-100">
      {/* Global Mission Control Header */}
      <Header
        telemetry={telemetry}
        isConnected={isConnected}
        onLoadDemo={loadDemoRefactor}
        onToggleTaint={injectConfidentialTaint}
      />

      {/* Floating Real-Time Telemetry Toast Notification */}
      {failoverToast && (
        <div className="w-full bg-surfaceHover/90 border-b border-borderDark px-4 py-2 flex items-center justify-between text-xs font-mono text-cyan-300 animate-fadeIn">
          <div className="flex items-center gap-2">
            <Bell className="w-3.5 h-3.5 text-brandCyan flex-shrink-0 animate-pulse" />
            <span>{failoverToast}</span>
          </div>
          <button
            onClick={() => setFailoverToast(null)}
            className="text-slate-400 hover:text-white px-2 py-0.5 rounded text-[11px]"
          >
            &times; Dismiss
          </button>
        </div>
      )}

      {/* 4-Panel Cyber-Institutional 2x2 Grid */}
      <div className="flex-1 p-3 md:p-4 grid grid-cols-1 xl:grid-cols-2 gap-3.5 max-w-[1920px] w-full mx-auto">
        {/* TOP ROW: Panels 1 & 2 */}
        <section className="h-[460px] xl:h-[490px]">
          <Panel1_ASTGraph
            nodes={telemetry.nodes}
            rawTotalTokens={telemetry.rawTotalTokens}
            prunedTotalTokens={telemetry.prunedTotalTokens}
            tokenSavingsPct={telemetry.tokenSavingsPct}
          />
        </section>

        <section className="h-[460px] xl:h-[490px]">
          <Panel2_ChaosBudget
            telemetry={telemetry}
            onTriggerChaos={triggerChaosOutage}
            onResetChaos={resetChaos}
            onUpdateBudget={updateBudgetCap}
          />
        </section>

        {/* BOTTOM ROW: Panels 3 & 4 */}
        <section className="h-[490px] xl:h-[510px]">
          <Panel3_TavilyScorecard
            claims={telemetry.claims}
            onApplyFreshPatch={applyFreshPatch}
          />
        </section>

        <section className="h-[490px] xl:h-[510px]">
          <Panel4_MonacoVoiceGate
            quarantinedAction={telemetry.quarantinedAction}
            onApproveAction={approveAction}
          />
        </section>
      </div>

      {/* Institutional Mission Control Footer Bar */}
      <footer className="w-full border-t border-borderDark/80 bg-surface/90 px-4 py-2 flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-400">
        <div className="flex items-center gap-3">
          <span className="text-slate-200 font-semibold">AEGIS-0 v2.0</span>
          <span>Bifrost AI Gateway (Maxim AI)</span>
          <span>&bull;</span>
          <span>Tavily Real-Time Web Verification</span>
          <span>&bull;</span>
          <span>Omnidimension Voice AI Gate</span>
          <span>&bull;</span>
          <span>Tree-Sitter Submodular AST Pruning</span>
        </div>
        <div className="flex items-center gap-2 text-slate-500">
          <span>Active Session ID: ses_aegis_master_001</span>
          <span>&bull;</span>
          <span>Dual Approval Standard (Visual Diff + Acoustic Biometrics)</span>
        </div>
      </footer>
    </main>
  );
}
