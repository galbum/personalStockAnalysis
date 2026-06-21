"""LLM narrative layer (Anthropic).

Feeds the real, computed pillar data plus the skill's own instruction files to
Claude, which acts as the orchestrating lead analyst: it interprets each pillar,
assigns verdicts, writes the thesis, and emits the Claude Design deck prompt.

Falls back gracefully -- if no API key or the call fails, the dashboard still
shows all real data and the rule-based verdicts.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

SKILL_DIR = Path(__file__).resolve().parent.parent / "skills" / "fundamental-analysis"

SKILL_FILES = [
    "SKILL.md",
    "references/data-sources.md",
    "references/metric-definitions.md",
    "agents/profitability.md",
    "agents/valuation.md",
    "agents/cash-flow.md",
    "agents/financial-health.md",
    "agents/forward-signals.md",
    "assets/deck-prompt-template.md",
]


def _load_skill_context() -> str:
    parts = []
    for rel in SKILL_FILES:
        path = SKILL_DIR / rel
        try:
            parts.append(f"===== {rel} =====\n{path.read_text(encoding='utf-8')}")
        except Exception:
            continue
    return "\n\n".join(parts)


def _strip_raw(analysis: dict) -> dict:
    """Drop the bulky raw company bundles before sending to the model."""
    slim = {k: v for k, v in analysis.items() if k != "raw"}
    return slim


SYSTEM_PROMPT = (
    "You are the lead PhD equity analyst orchestrating the fundamental-analysis "
    "skill. You are given (1) the skill's own instruction files and (2) REAL, "
    "already-gathered fundamental data for a company and its competitors. "
    "Use ONLY the numbers provided -- do not invent figures. Where a value is "
    "null, treat it as 'n/a - not disclosed'. Stay in research mode (no buy/sell "
    "orders) and keep the disclaimer. Return STRICT JSON only, no prose outside it."
)

OUTPUT_SPEC = """
Return a single JSON object with EXACTLY this shape:

{
  "pillars": {
    "profitability":     {"verdict": "Strong|Adequate|Weak", "interpretation": "<3-5 sentences>", "watch_items": ["..."]},
    "valuation":         {"verdict": "...", "interpretation": "...", "watch_items": ["..."]},
    "cash_flow":         {"verdict": "...", "interpretation": "...", "watch_items": ["..."]},
    "financial_health":  {"verdict": "...", "interpretation": "...", "watch_items": ["..."]},
    "forward_signals":   {"verdict": "...", "interpretation": "...", "watch_items": ["..."]}
  },
  "thesis": {
    "central_tension": "<one sentence>",
    "summary": "<3-5 sentence plain-English thesis>",
    "bull": ["...", "..."],
    "bear": ["...", "..."],
    "risks": ["...", "..."]
  },
  "deck_prompt": "<the full Claude Design prompt, following assets/deck-prompt-template.md, with the REAL numbers embedded>"
}
"""


def resolve_competitors(target: dict, model: str, api_key: str) -> list:
    """Ask Claude for two direct-competitor tickers for the target company."""
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    prompt = (
        f"Company: {target.get('name')} ({target.get('ticker')}), "
        f"sector: {target.get('sector')}, industry: {target.get('industry')}.\n"
        "Return ONLY a JSON array of exactly two stock tickers (strings) for its "
        "closest direct public competitors (same sub-industry, comparable model). "
        'Example: ["MSFT", "GOOGL"]. No other text.'
    )
    msg = client.messages.create(
        model=model,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    text = text[text.find("[") : text.rfind("]") + 1]
    tickers = json.loads(text)
    return [str(t).strip().upper() for t in tickers][:2]


def generate_narrative(analysis: dict, model: str, api_key: str) -> dict:
    """Call Claude to produce interpretations, thesis and the deck prompt."""
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    skill_context = _load_skill_context()
    data_json = json.dumps(_strip_raw(analysis), indent=2, default=str)

    user_content = (
        "## SKILL INSTRUCTION FILES\n"
        f"{skill_context}\n\n"
        "## REAL GATHERED DATA (JSON)\n"
        "This is the data already pulled from primary market data for the target "
        "and its competitors. 'Peer median' is the median of the shown peers only.\n"
        f"```json\n{data_json}\n```\n\n"
        "## YOUR TASK\n"
        "Acting as the orchestrator in SKILL.md, synthesize the analysis from the "
        "data above and produce the deck prompt from assets/deck-prompt-template.md.\n"
        f"{OUTPUT_SPEC}"
    )

    msg = client.messages.create(
        model=model,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    # Extract the outermost JSON object.
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model did not return JSON.")
    return json.loads(text[start : end + 1])


def get_api_key() -> Optional[str]:
    return os.environ.get("ANTHROPIC_API_KEY")
