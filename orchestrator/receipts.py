"""
AEGIS-0 Per-Run Token Receipts

A receipt is a self-contained record of one orchestration run: what context
was sent versus what the repository would have cost, what the run actually
cost, which symbols were kept or stubbed, the freshness verdicts and their
sources, the action-gate outcome, and the audit-chain head at the time.
The receipt carries a SHA-256 over its own canonical JSON so it can be
checked for tampering after it is shared.
"""

import hashlib
import html
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _canonical(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def build_receipt(
    *,
    session_id: str,
    prompt: str,
    status: str,
    model_used: str,
    model_tier: str,
    failover_chain: List[str],
    raw_tokens: int,
    context_tokens: int,
    expansion_tokens: int,
    cached_prompt_tokens: int,
    cost_usd: float,
    unpruned_extra_cost_usd: float,
    selected_symbols: List[str],
    stubbed_count: int,
    expansions: List[str],
    freshness: List[Dict[str, Any]],
    action: Optional[Dict[str, Any]],
    privacy_tainted: bool,
    audit_head: Optional[str],
    audit_chain_valid: Optional[bool],
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    tokens_saved = max(0, raw_tokens - context_tokens - expansion_tokens)
    receipt: Dict[str, Any] = {
        "run_id": run_id or f"run_{uuid.uuid4().hex[:12]}",
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        # Never echo a prompt the privacy guard flagged as containing secrets.
        "prompt": "[REDACTED: privacy guard flagged sensitive content]" if privacy_tainted else prompt,
        "status": status,
        "model": {"used": model_used, "tier": model_tier, "failover_chain": failover_chain},
        "tokens": {
            "repository_raw": raw_tokens,
            "context_sent": context_tokens,
            "expansion": expansion_tokens,
            "saved": tokens_saved,
            "compression_ratio": round(tokens_saved / raw_tokens, 4) if raw_tokens else 0.0,
            "served_from_prompt_cache": cached_prompt_tokens,
        },
        "cost_usd": {
            "actual": round(cost_usd, 6),
            "avoided_by_pruning": round(max(0.0, unpruned_extra_cost_usd), 6),
            "without_pruning_estimate": round(cost_usd + max(0.0, unpruned_extra_cost_usd), 6),
        },
        "context": {
            "full_symbols": selected_symbols,
            "stubbed_symbol_count": stubbed_count,
            "expanded_on_request": expansions,
        },
        "freshness": [
            {
                "claim": v.get("claim"),
                "status": v.get("status"),
                "score": v.get("freshness_score"),
                "patched": bool(v.get("patch") and v["patch"].get("replacement_pattern")),
                "sources": [s.get("url") for s in v.get("sources", []) if s.get("url")],
            }
            for v in freshness
        ],
        "action_gate": action,
        "privacy": {"tainted": privacy_tainted, "airgap_locked": privacy_tainted},
        "audit": {"chain_head": audit_head, "chain_valid": audit_chain_valid},
    }
    receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt).encode("utf-8")).hexdigest()
    return receipt


def verify_receipt(receipt: Dict[str, Any]) -> bool:
    body = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest() == receipt.get("receipt_sha256")


def render_html(receipt: Dict[str, Any]) -> str:
    """Standalone, dependency-free HTML rendering (light/dark aware)."""
    e = lambda v: html.escape(str(v))  # noqa: E731
    t, c = receipt["tokens"], receipt["cost_usd"]

    def links(urls: List[str]) -> str:
        return "<br>".join('<a href="%s">%s</a>' % (e(u), e(u)) for u in urls[:3])

    def row(f: Dict[str, Any]) -> str:
        status = e(f["status"])
        return (
            f"<tr><td><code>{e(f['claim'])}</code></td>"
            f"<td class='{status.lower()}'>{status}</td>"
            f"<td>{e(f['score'])}</td><td>{'yes' if f['patched'] else 'no'}</td>"
            f"<td>{links(f['sources'])}</td></tr>"
        )

    fresh_rows = "".join(row(f) for f in receipt["freshness"]) or (
        "<tr><td colspan='5'>No third-party APIs in the generated code.</td></tr>"
    )

    action = receipt.get("action_gate") or {}
    action_html = (
        f"<p><code>{e(action.get('action_id'))}</code> &middot; {e(action.get('category'))} "
        f"&rarr; <code>{e(action.get('target'))}</code> &middot; {e(action.get('status'))}</p>"
        if action else "<p>No write or shell action proposed.</p>"
    )
    symbols = ", ".join(f"<code>{e(s)}</code>" for s in receipt["context"]["full_symbols"][:40]) or "none"

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AEGIS-0 Receipt {e(receipt['run_id'])}</title>
<style>
:root {{ --bg:#fff; --fg:#1a1a2e; --muted:#5c5c70; --line:#e3e3ea; --ok:#0f7b4f; --bad:#b42318; --accent:#6d28d9; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#0f0f17; --fg:#ececf3; --muted:#a0a0b4; --line:#2a2a3a; --ok:#4ade80; --bad:#f87171; --accent:#a78bfa; }} }}
body {{ background:var(--bg); color:var(--fg); font:15px/1.5 system-ui,sans-serif; max-width:860px; margin:0 auto; padding:24px 16px; }}
h1 {{ font-size:20px; margin:0 0 4px; }} h2 {{ font-size:15px; margin:28px 0 8px; color:var(--accent); }}
.muted {{ color:var(--muted); font-size:13px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; }}
.card {{ border:1px solid var(--line); border-radius:10px; padding:12px; }}
.card b {{ display:block; font-size:22px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }} td,th {{ border-bottom:1px solid var(--line); padding:6px 4px; text-align:left; vertical-align:top; }}
.stale {{ color:var(--bad); font-weight:600; }} .fresh {{ color:var(--ok); font-weight:600; }}
code {{ font-size:12.5px; word-break:break-all; }} a {{ color:var(--accent); }}
</style></head><body>
<h1>AEGIS-0 run receipt</h1>
<div class="muted">{e(receipt['run_id'])} &middot; {e(receipt['issued_at'])} &middot; session {e(receipt['session_id'])} &middot; {e(receipt['status'])}</div>
<p>{e(receipt['prompt'])}</p>
<h2>Tokens and cost</h2>
<div class="grid">
<div class="card"><span class="muted">Context sent</span><b>{t['context_sent']:,}</b><span class="muted">of {t['repository_raw']:,} raw</span></div>
<div class="card"><span class="muted">Tokens saved</span><b>{t['saved']:,}</b><span class="muted">{t['compression_ratio']*100:.1f}% compression</span></div>
<div class="card"><span class="muted">Actual cost</span><b>${c['actual']:.4f}</b><span class="muted">{e(receipt['model']['used'])}</span></div>
<div class="card"><span class="muted">Avoided by pruning</span><b>${c['avoided_by_pruning']:.4f}</b><span class="muted">est. ${c['without_pruning_estimate']:.4f} unpruned</span></div>
</div>
<p class="muted">Expanded on request: {t['expansion']:,} tokens &middot; served from prompt cache: {t['served_from_prompt_cache']:,} tokens
&middot; failover chain: {e(' → '.join(receipt['model']['failover_chain']) or 'none')}</p>
<h2>Context kept in full ({len(receipt['context']['full_symbols'])}; {receipt['context']['stubbed_symbol_count']} stubbed)</h2>
<p>{symbols}</p>
<h2>Freshness verification</h2>
<table><tr><th>Claim</th><th>Status</th><th>F(c)</th><th>Patched</th><th>Sources</th></tr>{fresh_rows}</table>
<h2>Action gate</h2>{action_html}
<h2>Integrity</h2>
<p class="muted">Audit chain head <code>{e(receipt['audit']['chain_head'])}</code> (valid: {e(receipt['audit']['chain_valid'])})<br>
Receipt SHA-256 <code>{e(receipt['receipt_sha256'])}</code></p>
</body></html>
"""
