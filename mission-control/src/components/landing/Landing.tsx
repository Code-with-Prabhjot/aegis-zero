"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import Orb from "./Orb";
import "./landing.css";

const SECTIONS = [
  { id: "top", label: "Aegis", orb: [28, 0, 1] },
  { id: "problem", label: "Problem", orb: [-34, 8, 0.55] },
  { id: "prune", label: "Prune", orb: [36, -6, 0.5] },
  { id: "flow", label: "Pipeline", orb: [0, 0, 1.35] },
  { id: "resilience", label: "Resilience", orb: [-36, 0, 0.5] },
  { id: "fresh", label: "Fresh", orb: [34, 10, 0.45] },
  { id: "gate", label: "Gate", orb: [-30, -4, 0.6] },
  { id: "faq", label: "FAQ", orb: [34, 0, 0.55] },
  { id: "go", label: "Launch", orb: [0, 0, 1.15] },
] as const;

/* ---------- 1. pruning demo (real greedy knapsack on example symbols) ---------- */
const SYMS = [
  ["authenticate_session", 1240, 0.94], ["verify_hmac_signature", 890, 0.91], ["dispatch_bifrost_proxy", 1450, 0.88],
  ["tavily_search_dispatcher", 2760, 0.86], ["audit_crypto_tokens", 1320, 0.82], ["calculate_margin", 1820, 0.22],
  ["export_telemetry_csv", 2100, 0.12], ["parse_legacy_ast_symbols", 4210, 0.15],
] as const;

function PruneDemo() {
  const [budget, setBudget] = useState(4500);
  const order = [...SYMS].sort((a, b) => b[2] / b[1] - a[2] / a[1]);
  const pick = new Set<string>();
  let used = 0;
  for (const [n, c] of order) if (used + c <= budget) { pick.add(n); used += c; }
  const raw = SYMS.reduce((s, x) => s + x[1], 0);
  const sent = SYMS.reduce((s, x) => s + (pick.has(x[0]) ? x[1] : 18), 0);
  return (
    <div className="glass demo">
      <div className="demo-top">
        <label>Context budget <b>{budget.toLocaleString()} tokens</b>
          <input type="range" min={0} max={9000} step={100} value={budget} onChange={(e) => setBudget(+e.target.value)} />
        </label>
        <div className="kpis">
          <span><em>{raw.toLocaleString()}</em>full repo</span>
          <span><em>{sent.toLocaleString()}</em>sent to model</span>
          <span className="hl"><em>{Math.round((1 - sent / raw) * 100)}%</em>saved</span>
        </div>
      </div>
      <ul className="syms">
        {SYMS.map(([n, c, r]) => (
          <li key={n} className={pick.has(n) ? "on" : ""}>
            <code>{pick.has(n) ? `def ${n}(...):  # full body` : `def ${n}(...): ...  # stub`}</code>
            <span>{pick.has(n) ? c : 18} tok · rel {r}</span>
          </li>
        ))}
      </ul>
      <p className="note">Illustrative example symbols. The real pruner uses the same idea: pick the most relevant code per token, stub the rest.</p>
    </div>
  );
}

/* ---------- 2. resilience demo ---------- */
function Resilience() {
  const [outage, setOutage] = useState(false);
  const [secret, setSecret] = useState(false);
  const active = secret ? 2 : outage ? 1 : 0;
  const chain = [
    ["Claude 3.5 Sonnet", "Primary · cloud"],
    ["GPT-4o", "Secondary · cloud"],
    ["DeepSeek-Coder (Ollama)", "Local · air-gapped"],
  ];
  return (
    <div className="glass demo">
      <div className="toggles">
        <button className={`tg ${outage ? "bad" : ""}`} disabled={secret} onClick={() => setOutage(!outage)}>
          {outage ? "Clear outage" : "Inject HTTP 429 outage"}
        </button>
        <button className={`tg ${secret ? "cy" : ""}`} onClick={() => setSecret(!secret)}>
          {secret ? "Repo is confidential" : "Mark repo confidential"}
        </button>
      </div>
      <div className="chain">
        {chain.map(([n, s], i) => (
          <div key={n} className={`node ${active === i ? "act" : ""} ${i === 0 && outage ? "down" : ""} ${i < 2 && secret ? "locked" : ""}`}>
            <b>{n}</b><span>{i === 0 && outage ? "HTTP 429" : i < 2 && secret ? "blocked by policy" : s}</span>
          </div>
        ))}
      </div>
      <p className="note">
        {secret ? "Confidential taint set: requests can only reach the local model. Output from the model cannot change this route."
          : outage ? "Provider failed: the session continues on the next model with its history intact (simulated)."
          : "Healthy: primary model handles the request."}
      </p>
    </div>
  );
}

/* ---------- 3. freshness demo ---------- */
const CLAIMS = [
  ["openai.ChatCompletion.create()", 22, "docs.openai.com/v1-migration"],
  ["stripe.Subscription.create()", 98, "stripe.com/docs/billing"],
  ["langchain.chat_models.ChatOpenAI", 41, "python.langchain.com/docs"],
] as const;

function Fresh() {
  const [fixed, setFixed] = useState(false);
  return (
    <div className="light-card">
      <div className="claims">
        {CLAIMS.map(([c, s, u], i) => {
          const sc = fixed && s < 70 ? 96 : s;
          return (
            <div key={c} className="claim">
              <div><code>{c}</code><small>{u}</small></div>
              <div className="meter"><i style={{ width: `${sc}%` }} className={sc < 70 ? "stale" : ""} /></div>
              <b className={sc < 70 ? "stale" : "fresh"}>{sc} {sc < 70 ? "STALE" : "FRESH"}</b>
            </div>
          );
        })}
      </div>
      <pre>{fixed ? "client = OpenAI()\nres = client.chat.completions.create(model=\"gpt-4o\", ...)" : "import openai\nres = openai.ChatCompletion.create(model=\"gpt-4\", ...)"}</pre>
      <button className="btn dark" onClick={() => setFixed(!fixed)}>{fixed ? "Undo" : "Apply Tavily fresh patch"}</button>
      <p className="note dark">Example scores for illustration. Live scoring needs a Tavily key.</p>
    </div>
  );
}

/* ---------- 4. approval gate (real HMAC via WebCrypto) ---------- */
function Gate() {
  const [tok, setTok] = useState("");
  const [done, setDone] = useState(false);
  const sign = useCallback(async () => {
    const enc = new TextEncoder();
    const key = await crypto.subtle.importKey("raw", enc.encode("demo-session-key"), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    const sig = await crypto.subtle.sign("HMAC", key, enc.encode("write_file|auth_middleware.py|diff_sha256|nonce"));
    setTok("sha256:" + Array.from(new Uint8Array(sig)).map((b) => b.toString(16).padStart(2, "0")).join(""));
  }, []);
  useEffect(() => { sign(); }, [sign]);
  return (
    <div className="glass demo">
      <ul className="acts">
        <li><span className="ok">AUTO</span> read_file · ast_search · tavily_verify</li>
        <li><span className="warn">HOLD</span> write_file → <code>auth_middleware.py</code></li>
        <li><span className="warn">HOLD</span> exec_shell → <code>pytest</code></li>
      </ul>
      <div className="tok"><small>Pending action token (HMAC-SHA256, computed in your browser)</small><code>{tok || "..."}</code></div>
      <button className={`btn ${done ? "ghost" : ""}`} onClick={() => setDone(!done)}>{done ? "Approved ✓  (click to reset)" : "Approve & execute"}</button>
    </div>
  );
}

const FAQ = [
  ["Does private code ever leave the machine?", "No. A rule-based scanner (not the model) marks a repo confidential and the network layer then only allows the local model."],
  ["What stops the agent from overspending?", "A worst-case cost is computed before every call. If it breaches the cap, Aegis-0 down-routes to a cheaper model or halts cleanly."],
  ["What if a provider goes down?", "Bifrost fails over to the next model while Aegis-0 keeps the conversation and tool state in a provider-neutral format."],
  ["Who approves writes and shell commands?", "You do. Reads are free, anything that changes files, runs commands or touches Git waits for a signed approval."],
] as const;

export default function Landing() {
  const [active, setActive] = useState(0);
  const [open, setOpen] = useState(0);
  const orbRef = useRef<HTMLDivElement>(null);
  const target = useRef<number[]>([28, 0, 1]);
  const cur = useRef<number[]>([28, 0, 1]);

  useEffect(() => {
    const io = new IntersectionObserver(
      (es) => es.forEach((e) => {
        if (e.isIntersecting) {
          const i = SECTIONS.findIndex((s) => s.id === e.target.id);
          setActive(i);
          target.current = [...SECTIONS[i].orb];
        }
      }),
      { rootMargin: "-45% 0px -45% 0px" }
    );
    SECTIONS.forEach((s) => { const el = document.getElementById(s.id); if (el) io.observe(el); });
    const rv = new IntersectionObserver(
      (es) => es.forEach((e) => e.isIntersecting && (e.target.classList.add("in"), rv.unobserve(e.target))),
      { threshold: 0.12 }
    );
    document.querySelectorAll(".lp .rv").forEach((el) => rv.observe(el));

    let raf = 0;
    const loop = () => {
      const c = cur.current, t = target.current;
      for (let i = 0; i < 3; i++) c[i] += (t[i] - c[i]) * 0.06;
      if (orbRef.current) orbRef.current.style.transform = `translate(${c[0]}vw,${c[1]}vh) scale(${c[2]})`;
      raf = requestAnimationFrame(loop);
    };
    loop();
    return () => { io.disconnect(); rv.disconnect(); cancelAnimationFrame(raf); };
  }, []);

  const go = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  return (
    <div className="lp">
      <div className="fx" aria-hidden>
        <div className="fx-glow g1" /><div className="fx-glow g2" /><div className="fx-grain" />
        <div className="orb" ref={orbRef}><div className="orb-halo" /><Orb size={620} /></div>
      </div>

      <header className="pill-nav">
        <a className="logo" onClick={() => go("top")}>AEGIS<i>0</i></a>
        <nav>
          {["problem", "prune", "resilience", "fresh", "faq"].map((id) => <a key={id} onClick={() => go(id)}>{SECTIONS.find((s) => s.id === id)!.label}</a>)}
        </nav>
        <Link className="btn sm" href="/workbench">Launch Mission Control</Link>
      </header>

      <aside className="rail">
        {SECTIONS.map((s, i) => (
          <button key={s.id} className={i === active ? "on" : ""} onClick={() => go(s.id)}><i />{s.label}</button>
        ))}
      </aside>

      <section id="top" className="sec hero">
        <div className="hero-copy">
          <span className="eyebrow rv">Zero-trust coding agent</span>
          <h1 className="rv">AEGIS<br /><span>ZERO</span></h1>
          <p className="rv">A coding agent that reads only what it needs, never leaks private code, checks its own facts against the live web, and asks before it changes anything.</p>
          <div className="cta rv">
            <Link className="btn" href="/workbench">Launch Mission Control <span>→</span></Link>
            <a className="btn ghost" onClick={() => go("problem")}>Learn more</a>
          </div>
        </div>
        <div className="scroll-hint">scroll</div>
      </section>

      <section id="problem" className="sec">
        <div className="wrap">
          <span className="eyebrow rv">The problem</span>
          <h2 className="rv">Agents are expensive, <em>out of date</em> and over-trusted.</h2>
          <div className="trio">
            {[
              ["01", "Token burn", "They re-read unchanged files every turn and pay for context they never needed."],
              ["02", "Stale knowledge", "They write code for library versions that no longer exist, and nobody checks."],
              ["03", "Too much trust", "Private code can be sent to the cloud, and one hidden prompt can trigger a destructive command."],
            ].map(([n, t, d], i) => (
              <article key={n} className="glass card rv" style={{ transitionDelay: `${i * 90}ms` }}>
                <span className="num">{n}</span><h3>{t}</h3><p>{d}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="prune" className="sec">
        <div className="wrap split">
          <div className="rv">
            <span className="eyebrow">Step 1 · Token-optimal context</span>
            <h2>Send the <em>signal</em>, stub the rest.</h2>
            <p>The repository becomes a graph of functions. A budgeted knapsack picks the most relevant code per token; everything else collapses into a one-line signature so types still make sense. Drag the budget.</p>
          </div>
          <div className="rv"><PruneDemo /></div>
        </div>
      </section>

      <section id="flow" className="sec">
        <div className="wrap">
          <span className="eyebrow rv center">The pipeline</span>
          <h2 className="rv center">Every request passes <em>seven gates</em>.</h2>
          <ol className="flow">
            {[
              ["Intent", "Task arrives from UI or CLI."], ["Privacy guard", "Entropy, policy file and git-remote scan."],
              ["AST pruner", "Knapsack context under a budget."], ["Budget ledger", "Worst-case cost checked before dispatch."],
              ["Bifrost", "Routing, caching, 429/5xx failover."], ["Freshness", "Claims verified live on Tavily."],
              ["Approval gate", "Signed approval for writes and shell."],
            ].map(([t, d], i) => (
              <li key={t} className="rv" style={{ transitionDelay: `${i * 70}ms` }}><span>{String(i + 1).padStart(2, "0")}</span><b>{t}</b><small>{d}</small></li>
            ))}
          </ol>
        </div>
      </section>

      <section id="resilience" className="sec">
        <div className="wrap split rev">
          <div className="rv"><Resilience /></div>
          <div className="rv">
            <span className="eyebrow">Step 2 · Resilient and private</span>
            <h2>Outages happen. <em>Sessions don’t die.</em></h2>
            <p>Provider down or rate-limited? The next model picks up mid-task. Confidential repo? The route is locked to a local model, and nothing the model says can unlock it. Try both switches.</p>
          </div>
        </div>
      </section>

      <section id="fresh" className="sec">
        <div className="wrap">
          <div className="light-wrap rv">
            <span className="eyebrow dark">Step 3 · Live verification</span>
            <h2 className="dark">Catch stale APIs <em>before</em> you do.</h2>
            <p className="dark">Version and API claims are pulled from generated code, checked against live documentation, scored 0–100, and anything under 70 is rewritten from the fresh docs.</p>
            <Fresh />
          </div>
        </div>
      </section>

      <section id="gate" className="sec">
        <div className="wrap split">
          <div className="rv">
            <span className="eyebrow">Step 4 · Human in the loop</span>
            <h2>Reads are free. <em>Writes are signed.</em></h2>
            <p>Anything that changes files, runs a command or touches Git is held behind an HMAC-signed approval, by click or by voice. A tampered diff invalidates the token.</p>
          </div>
          <div className="rv"><Gate /></div>
        </div>
      </section>

      <section id="faq" className="sec">
        <div className="wrap narrow">
          <span className="eyebrow rv center">FAQ</span>
          <h2 className="rv center">Questions, <em>answered.</em></h2>
          <div className="faq rv">
            {FAQ.map(([q, a], i) => (
              <div key={q} className={`q ${open === i ? "open" : ""}`}>
                <button onClick={() => setOpen(open === i ? -1 : i)}>{q}<i /></button>
                <div><p>{a}</p></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="go" className="sec final">
        <div className="wrap center">
          <h2 className="rv">Enter <em>Mission Control.</em></h2>
          <p className="rv">Watch pruning, failover, freshness and approvals happen in one workbench.</p>
          <div className="cta rv" style={{ justifyContent: "center" }}>
            <Link className="btn big" href="/workbench">Launch Mission Control <span>→</span></Link>
          </div>
        </div>
        <footer>AEGIS-0 · Built for the Geek Room Global AI Hackathon 2026 · PS-01 + PS-06</footer>
      </section>
    </div>
  );
}
