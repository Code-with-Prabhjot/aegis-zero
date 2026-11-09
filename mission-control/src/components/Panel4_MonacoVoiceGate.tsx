"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { QuarantinedAction } from "@/types";
import {
  ShieldAlert,
  ShieldCheck,
  Mic,
  MicOff,
  Volume2,
  FileDiff,
  CheckCircle2,
  Lock,
  Unlock,
  Radio,
  FileCode,
} from "lucide-react";

// Dynamically import Monaco DiffEditor with SSR disabled
const DiffEditor = dynamic(
  () => import("@monaco-editor/react").then((mod) => mod.DiffEditor),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full min-h-[220px] bg-[#0d1117] flex items-center justify-center text-xs font-mono text-slate-500">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-brandCyan animate-ping" />
          Loading Monaco Diff Inspector...
        </div>
      </div>
    ),
  }
);

interface Panel4Props {
  quarantinedAction: QuarantinedAction | null;
  onApproveAction: (actionId: string, hmacToken: string) => void;
}

export function Panel4_MonacoVoiceGate({
  quarantinedAction,
  onApproveAction,
}: Panel4Props) {
  const [isListening, setIsListening] = useState(false);
  const [speechTranscript, setSpeechTranscript] = useState<string | null>(null);
  const [voiceApproved, setVoiceApproved] = useState(false);
  const [waveformBars, setWaveformBars] = useState<number[]>([
    12, 28, 45, 20, 60, 35, 75, 40, 25, 55, 30, 15,
  ]);

  // Audio waveform animation when listening
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isListening) {
      interval = setInterval(() => {
        setWaveformBars(
          Array.from({ length: 12 }, () => Math.floor(Math.random() * 60) + 10)
        );
      }, 120);
    } else {
      setWaveformBars([8, 14, 22, 12, 28, 18, 30, 20, 15, 22, 12, 8]);
    }
    return () => clearInterval(interval);
  }, [isListening]);

  // Simulated Voice Approval Gate
  const handleToggleVoice = () => {
    if (voiceApproved || !quarantinedAction) return;

    if (!isListening) {
      setIsListening(true);
      setSpeechTranscript("Acoustic listener active... Say 'Approve Alpha-7'");

      // Simulate acoustic phrase matching after 1.6s
      setTimeout(() => {
        setSpeechTranscript(
          "Transcribed: 'Approve Alpha-7' [ACOUSTIC MATCH 99.8% - VERIFIED]"
        );
        setIsListening(false);
        setVoiceApproved(true);

        // Automatically trigger cryptographic approval gate
        onApproveAction(quarantinedAction.action_id, quarantinedAction.hmac_token);
      }, 1600);
    } else {
      setIsListening(false);
    }
  };

  const isQuarantined = quarantinedAction?.is_quarantined && !quarantinedAction?.is_approved && !voiceApproved;

  return (
    <div
      className={`flex flex-col h-full bg-surface border rounded-lg overflow-hidden shadow-lg transition-colors ${
        isQuarantined
          ? "border-brandRose/70 shadow-[0_0_15px_rgba(244,63,94,0.15)]"
          : "border-brandGreen/60 shadow-[0_0_15px_rgba(16,185,129,0.15)]"
      }`}
    >
      {/* Panel Header */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-surfaceHover/80 border-b border-borderDark">
        <div className="flex items-center gap-2">
          <FileDiff className="w-4 h-4 text-brandCyan" />
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-100">
            Panel 4 // Monaco Diff Inspector &amp; Omnidimension Voice Gate
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {isQuarantined ? (
            <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-red-950/80 border border-brandRose/70 text-brandRose font-semibold animate-pulse">
              <ShieldAlert className="w-3.5 h-3.5 text-brandRose" />
              MUTATION QUARANTINED
            </span>
          ) : (
            <span className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-950/70 border border-brandGreen/60 text-brandGreen font-semibold">
              <ShieldCheck className="w-3.5 h-3.5 text-brandGreen" />
              HMAC APPROVED &amp; COMMITTED
            </span>
          )}
        </div>
      </div>

      {/* Main Diff Editor View */}
      <div className="flex-1 min-h-[220px] relative bg-[#0d1117] overflow-hidden">
        {quarantinedAction ? (
          <DiffEditor
            height="100%"
            language="python"
            original={quarantinedAction.original_payload}
            modified={quarantinedAction.diff_payload}
            theme="vs-dark"
            options={{
              readOnly: true,
              minimap: { enabled: false },
              fontSize: 12,
              scrollBeyondLastLine: false,
              renderSideBySide: true,
              smoothScrolling: true,
              lineNumbersMinChars: 3,
            }}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-xs font-mono text-slate-500">
            No active diff in quarantine. Read-only commands execute autonomously.
          </div>
        )}

        {/* Floating Target File Badge */}
        {quarantinedAction && (
          <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2.5 py-1 rounded bg-black/80 backdrop-blur-md border border-slate-700 text-[10px] font-mono text-slate-300">
            <FileCode className="w-3 h-3 text-brandCyan" />
            <span>Target: {quarantinedAction.command_or_path}</span>
          </div>
        )}
      </div>

      {/* HMAC-SHA256 Quarantine & Voice Biometric Approval Drawer */}
      <div
        className={`p-3.5 border-t transition-colors ${
          isQuarantined
            ? "bg-red-950/30 border-brandRose/60"
            : "bg-emerald-950/20 border-brandGreen/50"
        }`}
      >
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
          {/* HMAC Token Verification Info */}
          <div className="md:col-span-7 space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-slate-400 uppercase">
                Cryptographic Gate:
              </span>
              <span
                className={`text-[10px] font-mono px-1.5 py-0.2 rounded font-semibold ${
                  isQuarantined
                    ? "text-brandRose bg-red-950 border border-brandRose/50"
                    : "text-brandGreen bg-emerald-950 border border-brandGreen/50"
                }`}
              >
                {isQuarantined ? "HOLD FOR APPROVAL" : "HMAC VALIDATED"}
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <Lock
                className={`w-3.5 h-3.5 flex-shrink-0 ${
                  isQuarantined ? "text-brandRose" : "text-brandGreen"
                }`}
              />
              <code className="text-[11px] font-mono text-slate-300 truncate max-w-full block bg-black/50 px-2 py-0.5 rounded border border-borderDark/60">
                {quarantinedAction?.hmac_token || "sha256:awaiting-mutation-hash"}
              </code>
            </div>

            <p className="text-[10px] text-slate-400 font-mono">
              Zero-Trust Invariant: Read ops auto-execute. All Writes/Git/Shell are halted until cryptographic or voice sign-off.
            </p>
          </div>

          {/* Omnidimension Voice Approval HUD & Trigger */}
          <div className="md:col-span-5 flex flex-col items-end justify-center space-y-2">
            {/* Audio Waveform + Acoustic Readout */}
            <div className="w-full flex items-center justify-between gap-2 bg-black/60 p-2 rounded border border-borderDark/80">
              <div className="flex items-center gap-1.5">
                <Volume2 className="w-3.5 h-3.5 text-brandCyan flex-shrink-0" />
                <span className="text-[10px] font-mono text-slate-300 truncate max-w-[150px]">
                  {speechTranscript || quarantinedAction?.acoustic_prompt || "Acoustic listener standby"}
                </span>
              </div>

              {/* Dynamic SVG Waveform Bars */}
              <div className="flex items-center gap-0.5 h-5 flex-shrink-0">
                {waveformBars.map((h, i) => (
                  <div
                    key={i}
                    className={`w-1 rounded-full transition-all duration-100 ${
                      isListening
                        ? "bg-brandRose shadow-[0_0_6px_#f43f5e]"
                        : voiceApproved
                        ? "bg-brandGreen"
                        : "bg-slate-600"
                    }`}
                    style={{ height: `${Math.min(20, Math.max(4, (h / 70) * 20))}px` }}
                  />
                ))}
              </div>
            </div>

            {/* Approval Action Buttons */}
            <div className="flex items-center gap-2 w-full justify-end">
              {/* Omnidimension Voice Button */}
              <button
                onClick={handleToggleVoice}
                disabled={!isQuarantined}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono font-semibold transition-all border shadow-sm active:scale-95 ${
                  !isQuarantined
                    ? "bg-surfaceHover/50 border-slate-700 text-slate-500 cursor-default"
                    : isListening
                    ? "bg-brandRose text-white border-rose-400 animate-pulse shadow-[0_0_12px_#f43f5e]"
                    : "bg-surfaceHover border-brandCyan/70 text-brandCyan hover:bg-cyan-950/40"
                }`}
                title="Simulate hands-free voice biometric approval via Omnidimension"
              >
                {isListening ? (
                  <Radio className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Mic className="w-3.5 h-3.5" />
                )}
                <span>
                  {isListening
                    ? "Listening..."
                    : voiceApproved
                    ? "Voice Approved"
                    : "Voice Sign-Off"}
                </span>
              </button>

              {/* Visual Click Button */}
              <button
                onClick={() => {
                  if (quarantinedAction) {
                    onApproveAction(
                      quarantinedAction.action_id,
                      quarantinedAction.hmac_token
                    );
                  }
                }}
                disabled={!isQuarantined}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono font-bold transition-all border shadow-md active:scale-95 ${
                  !isQuarantined
                    ? "bg-emerald-950/40 border-emerald-800 text-emerald-400 cursor-default"
                    : "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white border-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.3)]"
                }`}
              >
                {!isQuarantined ? (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                ) : (
                  <Unlock className="w-3.5 h-3.5" />
                )}
                <span>{!isQuarantined ? "Committed" : "[Approve & Commit]"}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
