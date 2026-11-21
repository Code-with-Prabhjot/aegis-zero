"use client";

import React, { useState, useRef, useEffect } from "react";
import { ASTGraphNode } from "@/types";
import { GitBranch, Layers, Code2, ShieldCheck, Search, ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

interface Panel1Props {
  nodes: ASTGraphNode[];
  rawTotalTokens: number;
  prunedTotalTokens: number;
  tokenSavingsPct: number;
  mode?: "simple" | "developer";
}

export function Panel1_ASTGraph({
  nodes,
  rawTotalTokens,
  prunedTotalTokens,
  tokenSavingsPct,
  mode = "simple",
}: Panel1Props) {
  const [selectedNodeId, setSelectedNodeId] = useState<string>("n_auth");
  const [viewMode, setViewMode] = useState<"all" | "selected" | "pruned">("all");
  const [codeTab, setCodeTab] = useState<"active" | "full" | "stub">("active");
  const [searchFilter, setSearchFilter] = useState<string>("");

  // Interactive Zoom & Pan State
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || nodes[0];

  // Auto-select first active (S*) node or nodes[0] when nodes array changes and selectedNodeId is missing
  useEffect(() => {
    if (nodes.length === 0) return;
    const exists = nodes.some((n) => n.id === selectedNodeId);
    if (!exists) {
      const firstSelected = nodes.find((n) => n.selected);
      setSelectedNodeId(firstSelected ? firstSelected.id : nodes[0].id);
    }
  }, [nodes, selectedNodeId]);

  const handleMouseDown = (e: React.MouseEvent) => {
    // Only pan on left-click on the canvas background
    if (e.button === 0) {
      setIsPanning(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isPanning) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => setIsPanning(false);
  const handleMouseLeave = () => setIsPanning(false);

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const filteredNodes = nodes.filter((n) => {
    if (viewMode === "selected") return n.selected;
    if (viewMode === "pruned") return !n.selected;
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-[#0d081c]/75 backdrop-blur-xl border border-purple-500/20 rounded-2xl overflow-hidden shadow-[0_0_30px_rgba(139,92,246,0.08)]">
      {/* Panel Top Header */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2 bg-[#140b2b]/70 border-b border-purple-500/20 gap-2">
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-lg bg-purple-500/15 border border-purple-500/30 flex items-center justify-center">
            <GitBranch className="w-3.5 h-3.5 text-cosmicFuchsia" />
          </div>
          <h2 className="text-xs font-display tracking-wider text-purple-100 uppercase">
            01 // AST Dependency Call-Graph &amp; Submodular Pruning
          </h2>
        </div>

        <div className="flex items-center gap-2">
          {/* Symbol Search Filter Input */}
          <div className="relative flex items-center">
            <Search className="w-3 h-3 text-purple-400/60 absolute left-2 pointer-events-none" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Filter AST nodes..."
              className="bg-[#0b0518] border border-purple-500/30 rounded-lg pl-7 pr-2 py-0.5 text-[11px] font-mono text-purple-100 placeholder-purple-400/40 w-36 sm:w-44 focus:outline-none focus:border-cosmicFuchsia/70 transition-all"
            />
            {searchFilter && (
              <button
                onClick={() => setSearchFilter("")}
                className="absolute right-1.5 text-[10px] text-purple-400/60 hover:text-purple-200"
              >
                &times;
              </button>
            )}
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setViewMode("all")}
              className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono transition-all ${
                viewMode === "all"
                  ? "bg-purple-600/30 text-white border border-purple-400/50 shadow-[0_0_10px_rgba(168,85,247,0.3)]"
                  : "text-purple-300/60 hover:text-purple-100 hover:bg-purple-900/20"
              }`}
            >
              All ({nodes.length})
            </button>
            <button
              onClick={() => setViewMode("selected")}
              className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono transition-all ${
                viewMode === "selected"
                  ? "bg-emerald-950/70 text-brandGreen border border-brandGreen/60 shadow-[0_0_10px_rgba(16,185,129,0.25)]"
                  : "text-purple-300/60 hover:text-purple-100 hover:bg-purple-900/20"
              }`}
            >
              Active S* ({nodes.filter((n) => n.selected).length})
            </button>
            <button
              onClick={() => setViewMode("pruned")}
              className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono transition-all ${
                viewMode === "pruned"
                  ? "bg-purple-900/40 text-purple-200 border border-purple-500/40 shadow-[0_0_10px_rgba(168,85,247,0.25)]"
                  : "text-purple-300/60 hover:text-purple-100 hover:bg-purple-900/20"
              }`}
            >
              Pruned ({nodes.filter((n) => !n.selected).length})
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area: 60% Left SVG Call-Graph, 40% Right Symbol Inspector */}
      <div className="relative flex-1 grid grid-cols-1 lg:grid-cols-12 min-h-0 overflow-hidden">
        {/* LEFT COLUMN: 60% -> Interactive SVG Canvas + Flamegraph */}
        <div className="lg:col-span-7 flex flex-col h-full min-h-0 border-b lg:border-b-0 lg:border-r border-purple-500/20">
          {/* Interactive SVG Call-Graph Canvas with Drag-Pan & Zoom */}
          <div
            className={`flex-1 min-h-0 relative overflow-hidden bg-[#070412]/80 select-none ${
              isPanning ? "cursor-grabbing" : "cursor-grab"
            }`}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseLeave}
          >
            {/* Smooth Zoom Controls */}
            <div className="absolute top-3 right-3 flex items-center gap-1 bg-[#0d081c]/90 backdrop-blur-md px-2 py-1 rounded-lg border border-purple-500/25 text-[10px] font-mono shadow-md z-10">
              <button
                type="button"
                onClick={() => setZoom((z) => Math.max(0.5, Number((z - 0.15).toFixed(2))))}
                className="p-1 rounded hover:bg-purple-800/40 text-purple-200 hover:text-white transition-all"
                title="Zoom Out"
              >
                <ZoomOut className="w-3 h-3" />
              </button>
              <span className="px-1 text-purple-200 font-semibold min-w-[36px] text-center">
                {Math.round(zoom * 100)}%
              </span>
              <button
                type="button"
                onClick={() => setZoom((z) => Math.min(2.5, Number((z + 0.15).toFixed(2))))}
                className="p-1 rounded hover:bg-purple-800/40 text-purple-200 hover:text-white transition-all"
                title="Zoom In"
              >
                <ZoomIn className="w-3 h-3" />
              </button>
              <button
                type="button"
                onClick={resetView}
                className="ml-1 px-1.5 py-0.5 rounded bg-purple-900/40 hover:bg-purple-800/60 text-purple-200 text-[9px] transition-all flex items-center gap-1"
                title="Reset 100%"
              >
                <RotateCcw className="w-2.5 h-2.5" />
                <span>Reset</span>
              </button>
            </div>

            <svg
              className="w-full h-full"
              viewBox="0 0 920 440"
              preserveAspectRatio="xMidYMid meet"
            >
              {/* Grid Pattern Background & Styling */}
              <defs>
                <pattern
                  id="graph-grid-cosmic"
                  width="32"
                  height="32"
                  patternUnits="userSpaceOnUse"
                >
                  <path
                    d="M 32 0 L 0 0 0 32"
                    fill="none"
                    stroke="#2e1065"
                    strokeWidth="0.6"
                    opacity="0.35"
                  />
                </pattern>
                <linearGradient id="edge-grad-s" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#d946ef" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#10b981" stopOpacity="0.9" />
                </linearGradient>
                <filter id="glow-emerald" x="-30%" y="-30%" width="160%" height="160%">
                  <feGaussianBlur stdDeviation="5" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <filter id="glow-fuchsia" x="-30%" y="-30%" width="160%" height="160%">
                  <feGaussianBlur stdDeviation="6" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
                <filter id="glow-hover" x="-30%" y="-30%" width="160%" height="160%">
                  <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="#d946ef" floodOpacity="0.5" />
                </filter>

                {/* Animated Edge Pulse Dash-Offset */}
                <style>{`
                  @keyframes edgePulseOffset {
                    from { stroke-dashoffset: 24; }
                    to { stroke-dashoffset: 0; }
                  }
                  .edge-flow-active {
                    stroke-dasharray: 6 6;
                    animation: edgePulseOffset 1.2s linear infinite;
                  }
                `}</style>
              </defs>

              <rect width="100%" height="100%" fill="url(#graph-grid-cosmic)" />

              {/* Transform Container for Pan & Zoom */}
              <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                {/* Connecting Dependency Edges */}
                {nodes.map((node) =>
                  node.connections.map((targetId) => {
                    const targetNode = nodes.find((n) => n.id === targetId);
                    if (!targetNode) return null;
                    const isBothSelected = node.selected && targetNode.selected;
                    return (
                      <g key={`${node.id}-${targetId}`}>
                        {/* Static Base Edge Line */}
                        <line
                          x1={node.x}
                          y1={node.y}
                          x2={targetNode.x}
                          y2={targetNode.y}
                          stroke={isBothSelected ? "#10b981" : "#582a85"}
                          strokeWidth={isBothSelected ? 2.2 : 1}
                          strokeDasharray={isBothSelected ? undefined : "3,3"}
                          opacity={isBothSelected ? 0.75 : 0.3}
                        />

                        {/* Animated Dash-Offset Data-Flow Pulse on Active S* Edges */}
                        {isBothSelected && (
                          <line
                            x1={node.x}
                            y1={node.y}
                            x2={targetNode.x}
                            y2={targetNode.y}
                            stroke="#d946ef"
                            strokeWidth={2.4}
                            className="edge-flow-active"
                            opacity={0.9}
                          />
                        )}
                      </g>
                    );
                  })
                )}

                {/* AST Nodes */}
                {filteredNodes.map((node) => {
                  const isSelectedTarget = selectedNodeId === node.id;
                  const isPromoted = node.selected;
                  const isSearchMatch =
                    searchFilter.trim() !== "" &&
                    node.name.toLowerCase().includes(searchFilter.toLowerCase());

                  return (
                    <g
                      key={node.id}
                      transform={`translate(${node.x}, ${node.y})`}
                      className="cursor-pointer group select-none"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedNodeId(node.id);
                      }}
                    >
                      {/* Search Filter Real-Time Highlight Halo */}
                      {isSearchMatch && (
                        <circle
                          r="32"
                          fill="#d946ef"
                          opacity="0.3"
                          filter="url(#glow-fuchsia)"
                          className="animate-ping"
                        />
                      )}

                      {/* Outer Glow Halo for Active S* Nodes */}
                      {isPromoted && !isSearchMatch && (
                        <circle
                          r="28"
                          fill="#10b981"
                          opacity="0.2"
                          filter="url(#glow-emerald)"
                          className="animate-pulse"
                        />
                      )}

                      {/* Outer Glow Halo for Selected Target Node */}
                      {isSelectedTarget && (
                        <rect
                          x="-58"
                          y="-23"
                          width="116"
                          height="46"
                          rx="10"
                          fill="none"
                          stroke={isSearchMatch ? "#38bdf8" : "#d946ef"}
                          strokeWidth="1.5"
                          opacity="0.85"
                          filter="url(#glow-fuchsia)"
                        />
                      )}

                      {/* Main Node Shell */}
                      <rect
                        x="-55"
                        y="-20"
                        width="110"
                        height="40"
                        rx="8"
                        fill={
                          isSearchMatch
                            ? "#2a0d45"
                            : isSelectedTarget
                            ? isPromoted
                              ? "#0c3b28"
                              : "#210f3d"
                            : isPromoted
                            ? "#0c281e"
                            : "#100924"
                        }
                        stroke={
                          isSearchMatch
                            ? "#d946ef"
                            : isSelectedTarget
                            ? "#d946ef"
                            : isPromoted
                            ? "#10b981"
                            : "#58307d"
                        }
                        strokeWidth={isSearchMatch ? 2 : isSelectedTarget ? 2 : isPromoted ? 1.5 : 1}
                        className="transition-all duration-150 group-hover:stroke-fuchsia-400 group-hover:stroke-[2px] group-hover:brightness-125"
                      />

                      {/* Node Label */}
                      <text
                        x="0"
                        y="-4"
                        textAnchor="middle"
                        fill={isSearchMatch ? "#fdf4ff" : isPromoted ? "#ecfdf5" : "#c4b5fd"}
                        fontSize="11"
                        fontFamily="monospace"
                        fontWeight={isPromoted || isSearchMatch ? "bold" : "normal"}
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
                        fill={isPromoted ? "#34d399" : "#a78bfa"}
                        fontSize="9"
                        fontFamily="monospace"
                      >
                        {isPromoted
                          ? `${node.tokenCost} tok (S*)`
                          : `STUB (-${node.tokensSaved})`}
                      </text>

                      {/* Type Indicator Dot */}
                      <circle
                        cx="-45"
                        cy="-12"
                        r="4"
                        fill={
                          node.type === "class"
                            ? "#d946ef"
                            : node.type === "import"
                            ? "#38bdf8"
                            : "#10b981"
                        }
                      />
                    </g>
                  );
                })}
              </g>
            </svg>

            {/* Canvas Floating Legend */}
            <div className="absolute bottom-3 left-3 flex flex-wrap items-center gap-2.5 bg-[#0d081c]/90 backdrop-blur-md px-3 py-1.5 rounded-full border border-purple-500/25 text-[10px] font-mono text-purple-200 shadow-lg">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_6px_#10b981]" />
                <span className="text-emerald-300 font-semibold">S* Active Context</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-900/80 border border-purple-500/60" />
                <span className="text-purple-300">Pruned 1-Line Stub</span>
              </span>
              <span className="text-purple-500/60">|</span>
              <span className="text-cosmicFuchsia font-medium">Submodular Knapsack</span>
            </div>
          </div>

          {/* Token Flamegraph Footer Bar */}
          <div className="px-4 py-2.5 bg-[#0a0517]/95 border-t border-purple-500/20">
            <div className="flex flex-wrap items-center justify-between text-xs font-mono mb-1.5">
              <div className="flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-cosmicFuchsia" />
                <span className="font-semibold text-purple-100">
                  {mode === "developer" ? "Context Knapsack Flamegraph:" : "Context Optimization:"}
                </span>
                <span className="text-brandGreen font-bold">
                  {prunedTotalTokens.toLocaleString()} tok active
                </span>
                <span className="text-purple-500/60">/</span>
                <span className="text-purple-400/60 line-through">
                  {rawTotalTokens.toLocaleString()} tok raw
                </span>
              </div>
              <span className="font-display text-xs text-brandGreen font-bold tracking-wide">
                -{tokenSavingsPct}% TOKENS SAVED
              </span>
            </div>

            {/* Visual Dual-Bar Flamegraph */}
            <div className="relative w-full h-3 bg-[#06030e] rounded-full overflow-hidden border border-purple-500/30 flex shadow-inner">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 shadow-[0_0_10px_#10b981]"
                style={{ width: `${Math.max(2, (prunedTotalTokens / (rawTotalTokens || 1)) * 100)}%` }}
                title={`Active Context S*: ${prunedTotalTokens} tokens`}
              />
              <div
                className="h-full bg-gradient-to-r from-purple-950/80 to-[#1e103a] opacity-90"
                style={{ width: `${100 - (prunedTotalTokens / (rawTotalTokens || 1)) * 100}%` }}
                title={`Pruned AST Savings: ${rawTotalTokens - prunedTotalTokens} tokens`}
              />
            </div>

            {mode === "developer" && (
              <div className="flex justify-between items-center text-[10px] font-mono text-purple-300/60 mt-1">
                <span>0 tokens</span>
                <span className="text-purple-300/80">1-Line Stubs Replaced -{tokenSavingsPct}% Context</span>
                <span>Ceiling B_context: 8,000 tok</span>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: 40% -> Spacious Symbol Inspector */}
        <div className="lg:col-span-5 flex flex-col h-full min-h-0 bg-[#0b0618]/90 overflow-hidden p-4 space-y-3">
          {!selectedNode ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-3">
              <Code2 className="w-8 h-8 text-purple-400/40" />
              <p className="text-xs font-mono text-purple-300/60">
                No AST symbols indexed yet — run an agent task above.
              </p>
            </div>
          ) : (
            <>
              {/* Header */}
          <div className="flex items-center justify-between pb-2.5 border-b border-purple-500/20">
            <div className="flex items-center gap-2">
              <Code2 className="w-4 h-4 text-cosmicFuchsia" />
              <span className="text-xs font-display tracking-wider text-purple-100 uppercase">
                Symbol Inspector
              </span>
            </div>
            <span
              className={`text-[10px] font-mono px-2.5 py-0.5 rounded-full font-semibold ${
                selectedNode.selected
                  ? "bg-emerald-950/80 border border-emerald-500/60 text-emerald-300 shadow-[0_0_8px_rgba(16,185,129,0.25)]"
                  : "bg-purple-950/60 border border-purple-500/40 text-purple-300"
              }`}
            >
              {selectedNode.selected ? "INCLUDED IN S*" : "PRUNED TO STUB"}
            </span>
          </div>

          {/* Symbol Meta Grid */}
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="bg-[#120a26]/80 p-2.5 rounded-xl border border-purple-500/20">
              <span className="text-[10px] text-purple-300/60 block mb-0.5">Symbol Name</span>
              <p className="font-bold text-white truncate" title={selectedNode.name}>
                {selectedNode.name}
              </p>
              <span className="text-[10px] text-purple-400/70 font-mono capitalize">
                Type: {selectedNode.type}
              </span>
            </div>
            <div className="bg-[#120a26]/80 p-2.5 rounded-xl border border-purple-500/20">
              <span className="text-[10px] text-purple-300/60 block mb-0.5">File Location</span>
              <p className="font-mono text-purple-200 truncate" title={selectedNode.file}>
                {selectedNode.file}
              </p>
              <span className="text-[10px] text-emerald-400 font-mono">
                Relevance: {(selectedNode.relevance * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {/* Token Economics Cards (Developer) or Clean Savings Summary (Simple) */}
          {mode === "developer" ? (
            <div className="grid grid-cols-3 gap-2 text-center font-mono">
              <div className="bg-[#120a26]/70 p-2 rounded-xl border border-purple-500/20">
                <span className="text-[9px] text-purple-300/60 block uppercase">Raw Cost</span>
                <span className="text-white font-bold text-xs">{selectedNode.tokenCost} tok</span>
              </div>
              <div className="bg-[#120a26]/70 p-2 rounded-xl border border-purple-500/20">
                <span className="text-[9px] text-purple-300/60 block uppercase">Pruned Cost</span>
                <span className="text-brandGreen font-bold text-xs">
                  {selectedNode.selected ? selectedNode.tokenCost : selectedNode.stubTokenCost} tok
                </span>
              </div>
              <div className="bg-[#120a26]/70 p-2 rounded-xl border border-purple-500/20">
                <span className="text-[9px] text-purple-300/60 block uppercase">Token Savings</span>
                <span className="text-cosmicFuchsia font-bold text-xs">
                  {selectedNode.selected ? "0 tok" : `-${selectedNode.tokensSaved} tok`}
                </span>
              </div>
            </div>
          ) : (
            <div className="bg-[#120a26]/80 px-3 py-2 rounded-xl border border-purple-500/20 flex items-center justify-between text-xs font-mono">
              <span className="text-purple-300/70">Context Impact:</span>
              <span className={selectedNode.selected ? "text-emerald-400 font-bold" : "text-cosmicFuchsia font-bold"}>
                {selectedNode.selected ? "Full Symbol Retained (Core Context)" : `1-Line Stub (-${selectedNode.tokensSaved} tok saved)`}
              </span>
            </div>
          )}

          {/* Spacious Code Viewer */}
          <div className="flex-1 min-h-0 flex flex-col bg-[#06030e] rounded-xl border border-purple-500/25 overflow-hidden">
            <div className="flex items-center justify-between px-3 py-1.5 bg-[#130a26]/80 border-b border-purple-500/20 text-[11px] font-mono">
              <span className="text-purple-300/70">
                {mode === "developer" ? "Context Representation" : "Source Code View"}
              </span>
              <div className="flex items-center gap-1">
                {mode === "developer" ? (
                  <>
                    <button
                      onClick={() => setCodeTab("active")}
                      className={`px-2 py-0.5 rounded text-[10px] transition-all ${
                        codeTab === "active"
                          ? "bg-purple-600/40 text-white font-semibold border border-purple-400/40"
                          : "text-purple-300/60 hover:text-white"
                      }`}
                    >
                      Active ({selectedNode.selected ? "Full" : "Stub"})
                    </button>
                    <button
                      onClick={() => setCodeTab("full")}
                      className={`px-2 py-0.5 rounded text-[10px] transition-all ${
                        codeTab === "full"
                          ? "bg-purple-600/40 text-white font-semibold border border-purple-400/40"
                          : "text-purple-300/60 hover:text-white"
                      }`}
                    >
                      Full AST Body
                    </button>
                    <button
                      onClick={() => setCodeTab("stub")}
                      className={`px-2 py-0.5 rounded text-[10px] transition-all ${
                        codeTab === "stub"
                          ? "bg-purple-600/40 text-white font-semibold border border-purple-400/40"
                          : "text-purple-300/60 hover:text-white"
                      }`}
                    >
                      1-Line Stub
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => setCodeTab("active")}
                      className={`px-2.5 py-0.5 rounded text-[10px] transition-all ${
                        codeTab === "active"
                          ? "bg-purple-600/50 text-white font-semibold border border-purple-400/40"
                          : "text-purple-300/60 hover:text-white"
                      }`}
                    >
                      Optimized Code
                    </button>
                    <button
                      onClick={() => setCodeTab("full")}
                      className={`px-2.5 py-0.5 rounded text-[10px] transition-all ${
                        codeTab === "full"
                          ? "bg-purple-600/50 text-white font-semibold border border-purple-400/40"
                          : "text-purple-300/60 hover:text-white"
                      }`}
                    >
                      Original Full Code
                    </button>
                  </>
                )}
              </div>
            </div>

            <div className="flex-1 min-h-0 p-3 overflow-auto">
              <pre className="text-xs font-mono text-purple-100 leading-relaxed whitespace-pre font-normal">
                {codeTab === "active"
                  ? selectedNode.selected
                    ? selectedNode.fullCode
                    : selectedNode.stubCode
                  : codeTab === "full"
                  ? selectedNode.fullCode
                  : selectedNode.stubCode}
              </pre>
            </div>
          </div>

          {/* Submodular Guarantee Footnote (Developer only) */}
          {mode === "developer" && (
            <div className="p-2.5 rounded-xl bg-[#120a26]/60 border border-purple-500/20 flex items-center justify-between text-[10px] font-mono text-purple-300/70">
              <span className="flex items-center gap-1 text-emerald-400">
                <ShieldCheck className="w-3.5 h-3.5" />
                Submodular Knapsack Optimal S*
              </span>
              <span className="text-purple-300 font-semibold">
                {selectedNode.selected ? "High-Relevance Core" : "Type Signature Preserved"}
              </span>
            </div>
          )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
