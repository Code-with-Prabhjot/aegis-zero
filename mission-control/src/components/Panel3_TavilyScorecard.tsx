"use client";

import React from "react";
import { FreshnessClaim } from "@/types";
import {
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Wrench,
  Clock,
  Search,
  BookOpen,
  Sparkles,
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
    <div className="flex flex-col h-full bg-[#0d081c]/75 backdrop-blur-xl border border-purple-500/20 rounded-2xl overflow-hidden shadow-[0_0_30px_rgba(139,92,246,0.08)]">
      {/* Panel Top Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#140b2b]/70 border-b border-purple-500/20">
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-lg bg-purple-500/15 border border-purple-500/30 flex items-center justify-center">
            <Search className="w-3.5 h-3.5 text-cosmicFuchsia" />
          </div>
          <h2 className="text-xs font-display tracking-wider text-purple-100 uppercase">
            Tavily Live Verification Scorecard (PS-06)
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {staleCount > 0 ? (
            <span className="flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-rose-950/80 border border-brandRose/70 text-brandRose font-semibold animate-pulse shadow-[0_0_8px_rgba(244,63,94,0.3)]">
              <AlertCircle className="w-3.5 h-3.5 text-brandRose" />
              {staleCount} STALE APIS DETECTED
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-950/70 border border-brandGreen/60 text-brandGreen font-semibold shadow-[0_0_8px_rgba(16,185,129,0.2)]">
              <CheckCircle2 className="w-3.5 h-3.5 text-brandGreen" />
              ALL CLAIMS VERIFIED FRESH
            </span>
          )}
        </div>
      </div>

      {/* Main Container */}
      <div className="p-3.5 space-y-3 flex-1 min-h-0 overflow-y-auto bg-[#070412]/80">
        {/* Mathematical Header Note */}
        <div className="p-2.5 rounded-xl bg-[#120a26]/80 border border-purple-500/20 flex flex-wrap items-center justify-between text-[11px] font-mono text-purple-300/80 gap-2">
          <span>
            Empirical Formula:{" "}
            <strong className="text-cosmicFuchsia">
              F(c_j) = 100 × [w₁·e^(-μΔt) + w₂·A_sem - w₃·I_dep]
            </strong>
          </span>
          <span className="text-purple-400/60 font-semibold">Threshold F &lt; 70 = STALE</span>
        </div>

        {/* Claims Cards List */}
        <div className="space-y-2.5">
          {claims.map((claim) => {
            const isFresh = claim.confidence_score >= 70;
            return (
              <div
                key={claim.claim_id}
                className={`p-3.5 rounded-xl border transition-all duration-200 ${
                  !isFresh
                    ? "bg-rose-950/20 border-rose-500/40 hover:border-rose-400 shadow-[0_0_15px_rgba(244,63,94,0.1)]"
                    : "bg-[#0e0722]/80 border-purple-500/20 hover:border-emerald-500/40"
                }`}
              >
                {/* Claim Statement & Status Badge */}
                <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                  <div className="flex-1 min-w-[200px]">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-[10px] font-mono text-purple-300/60 uppercase">
                        Claim {claim.claim_id}
                      </span>
                      {claim.applied && (
                        <span className="text-[10px] font-mono px-2 py-0.2 rounded-full bg-emerald-950 border border-emerald-500 text-emerald-300 font-semibold shadow-[0_0_6px_#10b981]">
                          PATCH APPLIED
                        </span>
                      )}
                    </div>
                    <code className="text-xs font-mono font-bold text-purple-100 bg-black/50 px-2 py-1 rounded-md border border-purple-500/25 block overflow-x-auto">
                      {claim.statement}
                    </code>
                  </div>

                  {/* Freshness Confidence Gauge */}
                  <div className="flex items-center gap-2.5">
                    <div className="text-right">
                      <span className="text-[10px] font-mono text-purple-300/60 block">
                        Freshness F(c_j)
                      </span>
                      <span
                        className={`text-sm font-display font-bold ${
                          isFresh ? "text-brandGreen" : "text-brandRose"
                        }`}
                      >
                        {claim.confidence_score}%
                      </span>
                    </div>

                    <span
                      className={`px-2.5 py-1 rounded-full text-[10px] font-mono font-bold uppercase border ${
                        isFresh
                          ? "bg-emerald-950/80 border-brandGreen/80 text-brandGreen"
                          : "bg-rose-950/90 border-brandRose/90 text-brandRose shadow-[0_0_10px_#f43f5e]"
                      }`}
                    >
                      {claim.status}
                    </span>
                  </div>
                </div>

                {/* Temporal Decay & Web Citations */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono pt-2 border-t border-purple-500/20">
                  <div className="flex items-center gap-1.5 text-purple-300/70">
                    <Clock className="w-3.5 h-3.5 text-purple-400/60 flex-shrink-0" />
                    <span>Age Δt: </span>
                    <span
                      className={
                        claim.delta_t_days > 180
                          ? "text-brandRose font-semibold"
                          : "text-purple-200"
                      }
                    >
                      {claim.delta_t_days} days
                    </span>
                    <span className="text-purple-500/60">|</span>
                    <span>A_sem: {(claim.semantic_agreement * 100).toFixed(0)}%</span>
                  </div>

                  <div className="flex items-center gap-1 text-purple-300/70 justify-start sm:justify-end">
                    <BookOpen className="w-3.5 h-3.5 text-cosmicFuchsia flex-shrink-0" />
                    <a
                      href={claim.citation_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-200 hover:text-white hover:underline truncate max-w-[220px] flex items-center gap-1"
                      title={claim.citation_title}
                    >
                      <span className="truncate">{claim.citation_title}</span>
                      <ExternalLink className="w-3 h-3 text-cosmicFuchsia flex-shrink-0" />
                    </a>
                  </div>
                </div>

                {/* 1-Click Apply Tavily Fresh Patch Trigger */}
                {!isFresh && !claim.applied && claim.suggested_patch && (
                  <div className="mt-2.5 pt-2 border-t border-rose-500/30 flex flex-wrap items-center justify-between gap-2">
                    <div className="text-[11px] font-mono text-rose-200">
                      <span>Upgrade: </span>
                      <code className="text-emerald-400 font-semibold bg-black/50 px-1.5 py-0.5 rounded border border-purple-500/20">
                        {claim.suggested_patch}
                      </code>
                    </div>

                    <button
                      onClick={() => onApplyFreshPatch(claim.claim_id)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-mono text-xs font-bold transition-all shadow-[0_0_12px_rgba(16,185,129,0.3)] active:scale-95 cursor-pointer border border-emerald-400/60"
                    >
                      <Wrench className="w-3.5 h-3.5 text-white" />
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
