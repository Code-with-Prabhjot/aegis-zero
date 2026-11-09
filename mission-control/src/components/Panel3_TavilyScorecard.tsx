"use client";

import React from "react";
import { FreshnessClaim } from "@/types";
import {
  Sparkles,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Wrench,
  Clock,
  Search,
  BookOpen,
} from "lucide-react";

interface Panel3Props {
  claims: FreshnessClaim[];
  onApplyFreshPatch: (claimId: string) => void;
}

export function Panel3_TavilyScorecard({
  claims,
  onApplyFreshPatch,
}: Panel3Props) {
  const staleCount = claims.filter((c) => c.is_stale).length;

  return (
    <div className="flex flex-col h-full bg-surface border border-borderDark rounded-lg overflow-hidden shadow-lg">
      {/* Panel Header */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-surfaceHover/80 border-b border-borderDark">
        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-brandCyan" />
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-100">
            Panel 3 // Tavily Stale-Answer &amp; Live Citation Scorecard (PS-06)
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {staleCount > 0 ? (
            <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-red-950/80 border border-brandRose/70 text-brandRose font-semibold animate-pulse">
              <AlertCircle className="w-3 h-3 text-brandRose" />
              {staleCount} STALE API DETECTED
            </span>
          ) : (
            <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950/70 border border-brandGreen/60 text-brandGreen font-semibold">
              <CheckCircle2 className="w-3 h-3 text-brandGreen" />
              ALL CLAIMS VERIFIED FRESH
            </span>
          )}
        </div>
      </div>

      {/* Main Container */}
      <div className="p-3.5 space-y-3 flex-1 overflow-y-auto bg-[#070b12]">
        {/* Mathematical Header Note */}
        <div className="p-2 rounded bg-surface/70 border border-borderDark/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span>
            Empirical Formula:{" "}
            <strong className="text-brandCyan">
              F(c_j) = 100 × [w₁·e^(-μΔt) + w₂·A_sem - w₃·I_dep]
            </strong>
          </span>
          <span className="text-slate-500">Threshold F &lt; 70 = STALE</span>
        </div>

        {/* Claims Cards List */}
        <div className="space-y-2.5">
          {claims.map((claim) => {
            const isFresh = claim.confidence_score >= 70;
            return (
              <div
                key={claim.claim_id}
                className={`p-3 rounded-lg border transition-all ${
                  !isFresh
                    ? "bg-red-950/20 border-brandRose/60 hover:border-brandRose"
                    : "bg-surface/80 border-borderDark hover:border-emerald-500/50"
                }`}
              >
                {/* Claim Statement & Status Badge */}
                <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                  <div className="flex-1 min-w-[200px]">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="text-[10px] font-mono text-slate-500 uppercase">
                        Claim {claim.claim_id}
                      </span>
                      {claim.applied && (
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-950 border border-emerald-500 text-emerald-300 font-semibold">
                          PATCH APPLIED
                        </span>
                      )}
                    </div>
                    <code className="text-xs font-mono font-bold text-slate-100 bg-black/40 px-1.5 py-0.5 rounded border border-borderDark/50 block overflow-x-auto">
                      {claim.statement}
                    </code>
                  </div>

                  {/* Freshness Confidence Gauge */}
                  <div className="flex items-center gap-2">
                    <div className="text-right">
                      <span className="text-[10px] font-mono text-slate-400 block">
                        Freshness F(c_j)
                      </span>
                      <span
                        className={`text-sm font-mono font-bold ${
                          isFresh ? "text-brandGreen" : "text-brandRose"
                        }`}
                      >
                        {claim.confidence_score}%
                      </span>
                    </div>

                    <span
                      className={`px-2 py-1 rounded text-[11px] font-mono font-bold uppercase border ${
                        isFresh
                          ? "bg-emerald-950/80 border-brandGreen/80 text-brandGreen"
                          : "bg-red-950/90 border-brandRose/90 text-brandRose shadow-[0_0_8px_#f43f5e]"
                      }`}
                    >
                      {claim.status}
                    </span>
                  </div>
                </div>

                {/* Temporal Decay & Web Citations */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono pt-2 border-t border-borderDark/50">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                    <span>Age Δt: </span>
                    <span
                      className={
                        claim.delta_t_days > 180
                          ? "text-brandRose font-semibold"
                          : "text-slate-300"
                      }
                    >
                      {claim.delta_t_days} days
                    </span>
                    <span className="text-slate-600">|</span>
                    <span>A_sem: {(claim.semantic_agreement * 100).toFixed(0)}%</span>
                  </div>

                  <div className="flex items-center gap-1 text-slate-400 justify-start sm:justify-end">
                    <BookOpen className="w-3.5 h-3.5 text-brandCyan flex-shrink-0" />
                    <a
                      href={claim.citation_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-brandCyan hover:underline truncate max-w-[220px] flex items-center gap-1"
                      title={claim.citation_title}
                    >
                      <span className="truncate">{claim.citation_title}</span>
                      <ExternalLink className="w-3 h-3 flex-shrink-0" />
                    </a>
                  </div>
                </div>

                {/* 1-Click Apply Tavily Fresh Patch Trigger */}
                {!isFresh && !claim.applied && claim.suggested_patch && (
                  <div className="mt-2.5 pt-2 border-t border-brandRose/40 flex flex-wrap items-center justify-between gap-2">
                    <div className="text-[11px] font-mono text-rose-300">
                      <span>Suggested Fresh Upgrade: </span>
                      <code className="text-emerald-400 font-semibold bg-black/40 px-1 py-0.5 rounded">
                        {claim.suggested_patch}
                      </code>
                    </div>

                    <button
                      onClick={() => onApplyFreshPatch(claim.claim_id)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-brandGreen/20 hover:bg-brandGreen/30 border border-brandGreen text-brandGreen font-mono text-xs font-bold transition-all shadow-[0_0_10px_rgba(16,185,129,0.2)] active:scale-95"
                    >
                      <Wrench className="w-3.5 h-3.5 text-brandGreen" />
                      <span>[Apply Tavily Fresh Patch]</span>
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
