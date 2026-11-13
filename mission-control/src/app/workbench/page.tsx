"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { Panel1_ASTGraph } from "@/components/Panel1_ASTGraph";
import { Panel2_ChaosBudget } from "@/components/Panel2_ChaosBudget";
import { Panel3_TavilyScorecard } from "@/components/Panel3_TavilyScorecard";
import { Panel4_MonacoVoiceGate } from "@/components/Panel4_MonacoVoiceGate";
import { useOrchestrator } from "@/hooks/useOrchestrator";
import { Bell } from "lucide-react";

export default function MissionControlPage() {
  const [activeStage, setActiveStage] = useState<1 | 2 | 3>(1);
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

  // Keyboard shortcut listener for switching stages via keys 1, 2, 3
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const activeTag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (
        activeTag === "input" ||
        activeTag === "textarea" ||
        (e.target as HTMLElement)?.isContentEditable
      ) {
        return;
      }
      if (e.key === "1") setActiveStage(1);
      if (e.key === "2") setActiveStage(2);
      if (e.key === "3") setActiveStage(3);
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <main className="h-screen max-h-screen overflow-hidden flex flex-col bg-[#06040e] text-slate-100 relative">
      {/* Ambient Cosmic Atmosphere Background */}
      <div className="cosmic-atmosphere" />

      {/* Sleek Floating Pill Header */}
      <Header
        telemetry={telemetry}
        isConnected={isConnected}
        onLoadDemo={loadDemoRefactor}
        onToggleTaint={injectConfidentialTaint}
        activeStage={activeStage}
        onSelectStage={setActiveStage}
      />

      {/* Floating Real-Time Telemetry Toast Notification */}
      {failoverToast && (
        <div className="px-4 py-1 z-50 flex-shrink-0">
          <div className="max-w-[1920px] mx-auto bg-[#170e30]/95 border border-purple-500/40 px-4 py-2 rounded-xl flex items-center justify-between text-xs font-mono text-purple-200 shadow-[0_0_20px_rgba(168,85,247,0.3)] animate-fadeIn">
            <div className="flex items-center gap-2">
              <Bell className="w-3.5 h-3.5 text-cosmicFuchsia flex-shrink-0 animate-pulse" />
              <span>{failoverToast}</span>
            </div>
            <button
              onClick={() => setFailoverToast(null)}
              className="text-purple-300 hover:text-white px-2 py-0.5 rounded text-[11px]"
            >
              &times; Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Spacious 3-Stage Focused Workspace Views (calc(100vh - 88px)) */}
      <div className="flex-1 min-h-0 px-3 md:px-4 pb-2 pt-1 relative z-10 w-full max-w-[1920px] mx-auto">
        {/* STAGE 01: AST Context Pruner */}
        {activeStage === 1 && (
          <div className="h-full animate-fadeIn min-h-0">
            <Panel1_ASTGraph
              nodes={telemetry.nodes}
              rawTotalTokens={telemetry.rawTotalTokens}
              prunedTotalTokens={telemetry.prunedTotalTokens}
              tokenSavingsPct={telemetry.tokenSavingsPct}
            />
          </div>
        )}

        {/* STAGE 02: Bifrost & Budget */}
        {activeStage === 2 && (
          <div className="h-full animate-fadeIn min-h-0">
            <Panel2_ChaosBudget
              telemetry={telemetry}
              onTriggerChaos={triggerChaosOutage}
              onResetChaos={resetChaos}
              onUpdateBudget={updateBudgetCap}
            />
          </div>
        )}

        {/* STAGE 03: Tavily & Monaco Voice Gate */}
        {activeStage === 3 && (
          <div className="h-full grid grid-cols-1 lg:grid-cols-12 gap-3.5 animate-fadeIn min-h-0">
            {/* 42% Left Column: Panel 3 Tavily Scorecard */}
            <div className="lg:col-span-5 h-full min-h-0">
              <Panel3_TavilyScorecard
                claims={telemetry.claims}
                onApplyFreshPatch={applyFreshPatch}
              />
            </div>

            {/* 58% Right Column: Panel 4 Monaco Voice Gate */}
            <div className="lg:col-span-7 h-full min-h-0">
              <Panel4_MonacoVoiceGate
                quarantinedAction={telemetry.quarantinedAction}
                onApproveAction={approveAction}
              />
            </div>
          </div>
        )}
      </div>

      {/* Institutional Mission Control Micro-Footer Bar */}
      <footer className="w-full border-t border-purple-500/20 bg-[#0a0517]/90 px-4 py-1.5 flex flex-wrap items-center justify-between text-[11px] font-mono text-purple-300/60 z-20 flex-shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-purple-100 font-semibold font-display text-[10px]">
            AEGIS-0 v2.0
          </span>
          <span>Bifrost AI Gateway (Maxim AI)</span>
          <span>&bull;</span>
          <span>Tavily Real-Time Web Verification</span>
          <span>&bull;</span>
          <span>Omnidimension Voice AI Gate</span>
          <span>&bull;</span>
          <span>Submodular Knapsack AST Pruning</span>
        </div>
        <div className="flex items-center gap-2 text-purple-400/50">
          <span>Active Session ID: ses_aegis_master_001</span>
          <span>&bull;</span>
          <span>Dual Approval Standard (Visual Diff + Acoustic Biometrics)</span>
        </div>
      </footer>
    </main>
  );
}
