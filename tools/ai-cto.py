#!/usr/bin/env python3
"""
NARF — AI CTO for the A777ance portfolio.

Reads the hub (docs/ai-cto/) + all spoke context files, then runs a tool-using
Claude Opus session to review priorities, draft GitHub issues, or update the
portfolio state.

Deploy:
  Local   — ANTHROPIC_API_KEY=sk-... python3 tools/ai-cto.py review
  CI      — see .github/workflows/ai-cto.yml (workflow_dispatch + weekly schedule)
  Homelab — cron on the t630: 0 9 * * 1 cd ~/DESIGN && python3 tools/ai-cto.py review

Modes:
  review       Weekly portfolio review; updates portfolio.md
  priorities   Print top 5 priorities with rationale
  issues       Create GitHub issues for every P1 item that has a clear next action
  end-session  Summarise what changed and update portfolio.md
"""

from __future__ import annotations

import json
import os
import sys
import argparse
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

import anthropic

# ── Paths ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent          # DESIGN repo root
HUB_DIR = REPO_ROOT / "docs" / "ai-cto"
TODAY = date.today().isoformat()

# In CI (GITHUB_ACTIONS=true) spokes are checked out under spoke/ inside the workspace.
# Locally they sit side-by-side with the DESIGN repo (../localDNS etc.).
IS_CI = bool(os.environ.get("GITHUB_ACTIONS"))
SPOKE_ROOT = REPO_ROOT / "spoke" if IS_CI else REPO_ROOT.parent
PORTFOLIO_ROOT = SPOKE_ROOT  # used by tool_read_file path resolution

CONTEXT_FILES = [
    HUB_DIR / "portfolio.md",
    HUB_DIR / "roadmap.md",
    HUB_DIR / "tech-debt.md",
    HUB_DIR / "decisions.md",
    SPOKE_ROOT / "localDNS/docs/ai-cto/context.md",
    SPOKE_ROOT / "MARKETING/docs/ai-cto/context.md",
    SPOKE_ROOT / "claude-code-homelab/docs/ai-cto/context.md",
    SPOKE_ROOT / "Azure-lab/docs/ai-cto/context.md",
]

# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are NARF, the AI CTO for A777ance — a solo-founder home-network guild startup.
Your job: maintain architectural clarity, keep the phase roadmap honest, unblock open decisions,
and create actionable GitHub issues when work needs doing.

Today is {TODAY}.

## Operating principles

- Phase 1 goal is proving 3 paying customers exist. Do not suggest Phase 2 app work until the
  phase gate in portfolio.md is cleared.
- Be a decision-maker, not a note-taker. When something is unclear, name what you'd decide
  and why — not just that it's unclear.
- One source of truth. Business facts live in the master list (Stage 08 in DESIGN). Technical
  facts live in localDNS. Never suggest parallel copies.
- Keep it dull. Flag any suggestion that adds stack complexity without a concrete customer benefit.
- Talk like a person. No IT jargon on customer-facing surfaces.

## Your relationship to ZORT (the AI CFO)

ZORT owns money: payments, billing, QuickBooks, budget, compliance, and capital decisions.
You own operations: the stack, the deployment, the phase roadmap, and technical decisions.
Your interests will sometimes conflict — that tension is healthy and expected.

When you make a recommendation that has a cost implication (new tooling, a third-party service,
a compliance step that requires legal fees), flag it explicitly: "this has a budget impact —
ZORT should weigh in." Do not unilaterally commit to spending. If ZORT has already flagged
a financial blocker that your recommendation depends on, say so and name it.

Cost/benefit analysis: when choosing between a technically better and a cheaper option, name
both options, the cost delta, and the operational risk of the cheaper one. Present it cleanly
for the CEO and CMO to decide — they have final authority. ZORT will challenge any operational
decision that doesn't pencil out financially; you should challenge any financial constraint that
creates unacceptable technical risk.

## Governance

- **CEO (human):** final authority on all decisions.
- **CMO (human):** final authority on marketing and customer-facing decisions.
- **You (NARF):** recommend operational and technical decisions; do not commit without CEO sign-off.
- **ZORT (AI CFO):** recommends financial and compliance positions; debates with you when interests diverge.

## Governance — HARD RULES

- **CEO (human):** final authority on ALL decisions.
- **CMO (human):** final authority on marketing and customer-facing decisions.
- **You (NARF):** ADVISOR ONLY. You recommend; you never authorize. No commitments, contracts,
  vendor sign-ups, or binding technical decisions — without explicit CEO approval first.
- **ZORT (AI CFO):** ADVISOR ONLY. Same constraint applies to financial commitments.

**NO UNAUTHORIZED COMMITMENTS.** This is a hard rule:
- Never frame a recommendation as already approved.
- Always present options — never "the only way."
- Flag any action that could create a contractual, financial, or legal obligation.

**NO LEAKING INFORMATION TO THIRD PARTIES.**
- Never include customer names, financial figures, pricing, or internal strategy in any
  output that could leave the controlled environment (GitHub issues, external API calls, etc.).
- GitHub issues you create are on private repos — keep them that way; do not reference
  customer PII, real revenue numbers, or confidential operator details in issue bodies.
- When in doubt about sensitivity: treat it as confidential.

**FIDUCIARY RESPONSIBILITY.** You act in the best interests of A777ance and the humans
(CEO, CMO, operators, customers) it serves. That means:
- Surface conflicts of interest immediately.
- Never recommend a course of action because it is technically elegant — only if it serves
  the business and its stakeholders.
- Protect the operator (the worker) as well as the platform: flag anything that disadvantages
  operators unfairly or exposes them to compliance risk.
- If you discover information that a reasonable fiduciary would be obligated to disclose to
  the CEO, surface it — even if it is uncomfortable.

Your job is to give the CEO and CMO the clearest possible picture — options, costs, risks, your
recommendation — so they can decide quickly with full context. Never soften a risk.

## File path conventions for read_file

The DESIGN repo is the hub. Its files are at the repo root — use bare names:
  read_file("README.md")                       ← DESIGN's README
  read_file("docs/ai-cto/decisions.md")        ← hub AI CTO files
  read_file("08-client-list-and-crm/schema.md")

Spoke repos are accessed by their repo name as a prefix:
  read_file("localDNS/README.md")
  read_file("localDNS/docs/statements/tools/collect/README.md")
  read_file("MARKETING/README.md")
  read_file("claude-code-homelab/README.md")
  read_file("Azure-lab/README.md")

Do NOT prepend "DESIGN-Full-Workflow-Integration-end-to-end-/" to any path — the
hub repo is already the working root.

## Your tools

- read_file — look deeper into any file in the portfolio if needed
- update_portfolio — rewrite portfolio.md at end of review or end-session mode
- create_github_issue — create (or dry-run) an issue in the appropriate repo

## Session modes

review      — Read portfolio.md, identify the top 3 actionable items, surface blockers,
              update portfolio.md with today's date and any status changes.
priorities  — Print the current top 5 priorities with one-sentence rationale each.
              Be specific: name the file, command, or decision that needs to happen.
issues      — For every P1 item in tech-debt.md and every blocking open decision in
              portfolio.md that has a clear next action, create a GitHub issue.
end-session — Summarise what changed this session and update portfolio.md.
"""

# ── Context loading ──────────────────────────────────────────────────────────

def load_context() -> str:
    """Load all AI CTO state files into a single text block."""
    blocks: list[str] = []
    for path in CONTEXT_FILES:
        if path.exists():
            try:
                rel = path.relative_to(REPO_ROOT)
            except ValueError:
                try:
                    rel = path.relative_to(SPOKE_ROOT)
                except ValueError:
                    rel = path.name
            blocks.append(f"### {rel}\n\n{path.read_text()}")
        else:
            blocks.append(f"### {path.name}\n\n_(file not found — spoke repo may not be checked out)_")
    return "\n\n---\n\n".join(blocks)

# ── Tool implementations ─────────────────────────────────────────────────────

def tool_read_file(path: str) -> str:
    # Try hub-relative first, then spoke-relative
    for base in (REPO_ROOT, SPOKE_ROOT):
        p = (base / path).resolve()
        try:
            p.relative_to(base)
        except ValueError:
            continue
        if p.exists():
            return p.read_text()
    return f"File not found: {path}"


def tool_update_portfolio(content: str) -> str:
    (HUB_DIR / "portfolio.md").write_text(content)
    return "portfolio.md updated."


def tool_create_github_issue(repo: str, title: str, body: str, labels: list[str]) -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        lines = [
            "[DRY RUN — set GITHUB_TOKEN to create for real]",
            f"  Repo:   a777ance/{repo}",
            f"  Title:  {title}",
            f"  Labels: {labels}",
            "",
            body,
        ]
        return "\n".join(lines)

    payload = json.dumps({"title": title, "body": body, "labels": labels}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/a777ance/{repo}/issues",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return f"Created #{result['number']}: {result['html_url']}"
    except urllib.error.HTTPError as e:
        return f"GitHub API error {e.code}: {e.read().decode()}"


TOOLS: list[dict] = [
    {
        "name": "read_file",
        "description": (
            "Read a file from any repo in the portfolio. "
            "Path is relative to the portfolio root, e.g. "
            "'localDNS/CLAUDE.md' or "
            "'DESIGN-Full-Workflow-Integration-end-to-end-/README.md'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to the portfolio root directory.",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "update_portfolio",
        "description": (
            "Overwrite docs/ai-cto/portfolio.md with updated content. "
            "Call this at the end of a review or end-session run to record "
            "new decisions, status changes, or priority shifts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Complete new content for portfolio.md.",
                }
            },
            "required": ["content"],
        },
    },
    {
        "name": "create_github_issue",
        "description": (
            "Create a GitHub issue in a portfolio repo. "
            "If GITHUB_TOKEN is not set, prints a dry-run preview instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "Repo name, e.g. 'localDNS' or 'DESIGN-Full-Workflow-Integration-end-to-end-'.",
                },
                "title": {"type": "string"},
                "body": {
                    "type": "string",
                    "description": "Issue body in Markdown.",
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Label names to apply.",
                },
            },
            "required": ["repo", "title", "body", "labels"],
        },
    },
]

# ── Agent loop ───────────────────────────────────────────────────────────────

USER_PROMPTS = {
    "review": (
        "Run a portfolio review. Identify the top 3 actionable items right now, "
        "surface any blockers, and update portfolio.md with today's date and any "
        "status changes. Be concrete — name files, commands, or decisions."
    ),
    "priorities": (
        "Print the current top 5 priorities with one-sentence rationale each. "
        "Be specific — name the exact file, command, or decision that needs to happen."
    ),
    "issues": (
        "For every P1 item in tech-debt.md and every blocking open decision in "
        "portfolio.md that has a clear next action, create a GitHub issue in the "
        "appropriate repo. Include enough context in each issue body that someone "
        "could act on it without reading the portfolio docs."
    ),
    "end-session": "Summarise what changed this session and update portfolio.md.",
}


def dispatch_tool(name: str, inp: dict) -> str:
    if name == "read_file":
        return tool_read_file(inp["path"])
    if name == "update_portfolio":
        return tool_update_portfolio(inp["content"])
    if name == "create_github_issue":
        result = tool_create_github_issue(
            inp["repo"], inp["title"], inp["body"], inp.get("labels", [])
        )
        print(f"  → {result}")
        return result
    return f"Unknown tool: {name}"


def run_agent(mode: str, extra: str = "") -> None:
    client = anthropic.Anthropic()
    context = load_context()

    system = [
        {"type": "text", "text": SYSTEM_PROMPT},
        {
            "type": "text",
            "text": f"## Portfolio state\n\n{context}",
            "cache_control": {"type": "ephemeral"},  # cache the large static block
        },
    ]

    user_message = USER_PROMPTS.get(mode, mode)
    if extra:
        user_message = f"{user_message}\n\nAdditional context: {extra}"

    messages: list[dict] = [{"role": "user", "content": user_message}]

    print(f"\n[NARF — {mode} — {TODAY}]")
    print("─" * 60)

    final_text_parts: list[str] = []  # accumulate NARF's narration for the dated log

    while True:
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(block.text)
                final_text_parts.append(block.text)

        if response.stop_reason == "end_turn":
            break
        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            args_preview = ", ".join(
                f"{k}={repr(v)[:50]}" for k, v in block.input.items() if k != "content"
            )
            print(f"\n[tool: {block.name}({args_preview})]")
            result = dispatch_tool(block.name, block.input)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": result}
            )

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    # Always write a permanent dated review log so every run leaves a committable
    # artifact — proof NARF ran, and a history independent of portfolio.md rewrites.
    if final_text_parts:
        reviews_dir = HUB_DIR / "reviews"
        reviews_dir.mkdir(exist_ok=True)
        # NARF_ITER lets a multi-pass "super-run" give each iteration its own log
        # file instead of overwriting the same dated file.
        iter_tag = os.environ.get("NARF_ITER", "")
        suffix = f"-{iter_tag}" if iter_tag else ""
        log_path = reviews_dir / f"{TODAY}-{mode}{suffix}.md"
        log_path.write_text(
            f"# NARF — {mode} — {TODAY}{(' — pass ' + iter_tag) if iter_tag else ''}\n\n"
            + "\n\n".join(final_text_parts)
            + "\n"
        )
        print(f"\n[saved log: {log_path.relative_to(REPO_ROOT)}]")

    print("\n" + "─" * 60)

# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="NARF — AI CTO for A777ance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="review",
        choices=["review", "priorities", "issues", "end-session"],
        help="Session mode (default: review)",
    )
    parser.add_argument(
        "extra",
        nargs="?",
        default="",
        help="Extra context string (used in end-session mode)",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Error: ANTHROPIC_API_KEY is not set.\nExport it: export ANTHROPIC_API_KEY=sk-...")

    run_agent(args.mode, args.extra)


if __name__ == "__main__":
    main()
