"use client";

import React, { useState } from "react";
import { ASTGraphNode } from "@/types";
import { GitBranch, Layers, Sparkles, Code2, Eye, ShieldCheck } from "lucide-react";

interface Panel1Props {
  nodes: ASTGraphNode[];
  rawTotalTokens: number;
  prunedTotalTokens: number;
  tokenSavingsPct: number;
}

export function Panel1_ASTGraph({
  nodes,
  rawTotalTokens,
  prunedTotalTokens,
  tokenSavingsPct,
}: Panel1Props) {
  const [selectedNodeId, setSelectedNodeId] = useState<string>("n_auth");
  const [viewMode, setViewMode] = useState<"all" | "selected" | "pruned">("all");

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || nodes[0];

  const filteredNodes = nodes.filter((n) => {
    if (viewMode === "selected") return n.selected;
    if (viewMode === "pruned") return !n.selected;
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-surface border border-borderDark rounded-lg overflow-hidden shadow-lg">
      {/* Panel Header */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-surfaceHover/80 border-b border-borderDark">
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-brandCyan" />
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-100">
            Panel 1 // AST Dependency Call-Graph &amp; Submodular Pruning
          </h2>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setViewMode("all")}
            className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors ${
              viewMode === "all"
                ? "bg-brandCyan/20 text-brandCyan border border-brandCyan/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            All ({nodes.length})
          </button>
          <button
            onClick={() => setViewMode("selected")}
            className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors ${
              viewMode === "selected"
                ? "bg-brandGreen/20 text-brandGreen border border-brandGreen/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Active S* ({nodes.filter((n) => n.selected).length})
          </button>
          <button
            onClick={() => setViewMode("pruned")}
            className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors ${
              viewMode === "pruned"
                ? "bg-slate-700/50 text-slate-300 border border-slate-600"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Pruned Stubs ({nodes.filter((n) => !n.selected).length})
          </button>
        </div>
      </div>

      {/* Main Content Area: SVG Graph + Node Details */}
      <div className="relative flex-1 grid grid-cols-1 lg:grid-cols-12 min-h-[310px] overflow-hidden bg-[#070b12]">
        {/* SVG Force-Directed Call-Graph Canvas */}
        <div className="lg:col-span-8 relative h-full w-full min-h-[260px] overflow-hidden">
          <svg
            className="w-full h-full select-none"
            viewBox="0 0 920 500"
            preserveAspectRatio="xMidYMid meet"
          >
            {/* Grid Pattern Background */}
            <defs>
              <pattern
                id="graph-grid"
                width="30"
                height="30"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M 30 0 L 0 0 0 30"
                  fill="none"
                  stroke="#1e293b"
                  strokeWidth="0.6"
                  opacity="0.4"
                />
              </pattern>
              <linearGradient id="edge-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#10b981" stopOpacity="0.8" />
              </linearGradient>
              <filter id="glow-emerald" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            <rect width="100%" height="100%" fill="url(#graph-grid)" />

            {/* Connecting Dependency Edges */}
            {nodes.map((node) =>
              node.connections.map((targetId) => {
                const targetNode = nodes.find((n) => n.id === targetId);
                if (!targetNode) return null;
                const isBothSelected = node.selected && targetNode.selected;
                return (
                  <line
                    key={`${node.id}-${targetId}`}
                    x1={node.x}
                    y1={node.y}
                    x2={targetNode.x}
                    y2={targetNode.y}
                    stroke={isBothSelected ? "#10b981" : "#334155"}
                    strokeWidth={isBothSelected ? 2 : 1}
                    strokeDasharray={isBothSelected ? undefined : "3,3"}
                    opacity={isBothSelected ? 0.75 : 0.35}
                  />
                );
              })
            )}

            {/* AST Nodes */}
            {filteredNodes.map((node) => {
              const isSelectedTarget = selectedNodeId === node.id;
              const isPromoted = node.selected;

              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  className="cursor-pointer transition-transform duration-150 hover:scale-105"
                  onClick={() => setSelectedNodeId(node.id)}
                >
                  {/* Outer Glow Halo for Active S* Nodes */}
                  {isPromoted && (
                    <circle
                      r="26"
                      fill="#10b981"
                      opacity="0.18"
                      filter="url(#glow-emerald)"
                      className="animate-pulse"
                    />
                  )}

                  {/* Main Node Shell */}
                  <rect
                    x="-55"
                    y="-20"
                    width="110"
                    height="40"
                    rx="6"
                    fill={
                      isSelectedTarget
                        ? isPromoted
                          ? "#064e3b"
                          : "#1e293b"
                        : isPromoted
                        ? "#0f3529"
                        : "#111827"
                    }
                    stroke={
                      isSelectedTarget
                        ? "#38bdf8"
                        : isPromoted
                        ? "#10b981"
                        : "#334155"
                    }
                    strokeWidth={isSelectedTarget ? 2.5 : isPromoted ? 1.8 : 1}
                    className="transition-colors"
                  />

                  {/* Node Label */}
                  <text
                    x="0"
                    y="-4"
                    textAnchor="middle"
                    fill={isPromoted ? "#ecfdf5" : "#94a3b8"}
                    fontSize="11"
                    fontFamily="monospace"
                    fontWeight={isPromoted ? "bold" : "normal"}
                  >
                    {node.name.length > 14
                      ? node.name.slice(0, 13) + "…"
                      : node.name}
                  </text>

                  {/* Node Sub-Badge (Token Cost or Stub) */}
                  <text
                    x="0"
                    y="11"
                    textAnchor="middle"
                    fill={isPromoted ? "#34d399" : "#64748b"}
                    fontSize="9"
                    fontFamily="monospace"
                  >
                    {isPromoted
                      ? `${node.tokenCost} tok (S*)`
                      : `STUB (-${node.tokensSaved})`}
                  </text>

                  {/* Small Type Icon Marker */}
                  <circle
                    cx="-45"
                    cy="-12"
                    r="4"
                    fill={
                      node.type === "class"
                        ? "#a855f7"
                        : node.type === "import"
                        ? "#38bdf8"
                        : "#10b981"
                    }
                  />
                </g>
              );
            })}
          </svg>

          {/* Canvas Floating Legend */}
          <div className="absolute bottom-2 left-2 flex flex-wrap items-center gap-2 bg-surface/90 backdrop-blur-md px-2.5 py-1.5 rounded border border-borderDark/80 text-[10px] font-mono text-slate-300">
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 shadow-[0_0_6px_#10b981]" />
              S* Active Context
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-sm bg-slate-700 border border-slate-500" />
              Pruned 1-Line Stub
            </span>
            <span className="text-slate-500">|</span>
            <span className="text-brandCyan">Algorithm: Submodular Knapsack</span>
          </div>
        </div>

        {/* Selected AST Node Inspector Drawer */}
        <div className="lg:col-span-4 border-t lg:border-t-0 lg:border-l border-borderDark bg-surface/90 p-3 flex flex-col justify-between overflow-y-auto max-h-[330px]">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-borderDark">
              <span className="text-[11px] font-mono text-slate-400 uppercase">
                Symbol Inspector
              </span>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
                  selectedNode.selected
                    ? "bg-emerald-950/80 border border-emerald-500/60 text-emerald-300"
                    : "bg-slate-800 border border-slate-600 text-slate-300"
                }`}
              >
                {selectedNode.selected ? "INCLUDED IN S*" : "PRUNED TO STUB"}
              </span>
            </div>

            <div className="mt-2.5 space-y-2">
              <div>
                <span className="text-[10px] text-slate-500 font-mono">Symbol Name</span>
                <p className="text-xs font-mono font-bold text-slate-100 flex items-center gap-1">
                  <Code2 className="w-3.5 h-3.5 text-brandCyan" />
                  {selectedNode.name}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                <div className="bg-background/60 p-1.5 rounded border border-borderDark/60">
                  <span className="text-[10px] text-slate-500 block">Raw Cost</span>
                  <span className="text-slate-200 font-semibold">{selectedNode.tokenCost} tok</span>
                </div>
                <div className="bg-background/60 p-1.5 rounded border border-borderDark/60">
                  <span className="text-[10px] text-slate-500 block">Pruned Cost</span>
                  <span className="text-brandGreen font-semibold">
                    {selectedNode.selected ? selectedNode.tokenCost : selectedNode.stubTokenCost} tok
                  </span>
                </div>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 font-mono">Source Location</span>
                <p className="text-[11px] font-mono text-slate-300 truncate">
                  {selectedNode.file}
                </p>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 font-mono flex items-center justify-between">
                  <span>Context Representation</span>
                  <span className="text-brandCyan text-[9px]">
                    {selectedNode.selected ? "Full AST Body" : "1-Line Type Stub"}
                  </span>
                </span>
                <pre className="mt-1 p-2 rounded bg-black/60 border border-borderDark text-[10px] font-mono text-slate-300 overflow-x-auto max-h-[110px] leading-relaxed">
                  {selectedNode.selected ? selectedNode.fullCode : selectedNode.stubCode}
                </pre>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-borderDark/60 text-[10px] font-mono text-slate-400 flex items-center justify-between">
            <span>Relevance r(v,q): {(selectedNode.relevance * 100).toFixed(0)}%</span>
            <span className="text-emerald-400">
              {selectedNode.selected ? "Zero Quality Loss" : `Saved ${selectedNode.tokensSaved} tok`}
            </span>
          </div>
        </div>
      </div>

      {/* Token Flamegraph Footer Bar */}
      <div className="px-3.5 py-2.5 bg-surface/95 border-t border-borderDark">
        <div className="flex flex-wrap items-center justify-between text-xs font-mono mb-1.5">
          <div className="flex items-center gap-2">
            <Layers className="w-3.5 h-3.5 text-brandCyan" />
            <span className="font-semibold text-slate-200">
              Context Knapsack Flamegraph:
            </span>
            <span className="text-brandGreen font-bold">
              Input AST: {prunedTotalTokens.toLocaleString()} tok
            </span>
            <span className="text-slate-500">/</span>
            <span className="text-slate-400 line-through">
              Raw Codebase: {rawTotalTokens.toLocaleString()} tok
            </span>
          </div>
          <span className="text-brandGreen font-bold font-mono">
            -{tokenSavingsPct}% OPTIMIZATION (40,840 TOKENS SAVED)
          </span>
        </div>

        {/* Visual Dual-Bar Flamegraph */}
        <div className="relative w-full h-3 bg-slate-900 rounded-full overflow-hidden border border-slate-700/80 flex">
          {/* Pruned Context in S* */}
          <div
            className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 shadow-[0_0_8px_#10b981]"
            style={{ width: `${(prunedTotalTokens / rawTotalTokens) * 100}%` }}
            title={`Active Context S*: ${prunedTotalTokens} tokens`}
          />
          {/* Pruned Stub Savings */}
          <div
            className="h-full bg-gradient-to-r from-slate-700 to-slate-800 opacity-80"
            style={{ width: `${100 - (prunedTotalTokens / rawTotalTokens) * 100}%` }}
            title={`Pruned AST Savings: ${rawTotalTokens - prunedTotalTokens} tokens`}
          />
        </div>

        <div className="flex justify-between items-center text-[10px] font-mono text-slate-500 mt-1">
          <span>0 tokens</span>
          <span>1-Line Stubs Replaced 84% Context Body</span>
          <span>Ceiling B_context: 8,000 tok</span>
        </div>
      </div>
    </div>
  );
}
