#!/usr/bin/env python3
"""
ZORT — AI CFO for the A777ance portfolio.

Reads the hub (docs/ai-cfo/) + financial context files, then runs a tool-using
Claude Opus session to review financial health, track KPIs, or update the
financial portfolio state.

Deploy:
  Local   — ANTHROPIC_API_KEY=sk-... python3 tools/ai-cfo.py review
  CI      — see .github/workflows/ai-cfo.yml (workflow_dispatch + daily schedule)

Modes:
  review       Weekly financial review; updates portfolio.md
  metrics      Print current KPIs with actuals vs. targets
  forecast     Run a 90-day revenue/cost projection
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
HUB_DIR = REPO_ROOT / "docs" / "ai-cfo"
TODAY = date.today().isoformat()

# In CI (GITHUB_ACTIONS=true) spokes are checked out under spoke/ inside the workspace.
# Locally they sit side-by-side with the DESIGN repo (../localDNS etc.).
IS_CI = bool(os.environ.get("GITHUB_ACTIONS"))
SPOKE_ROOT = REPO_ROOT / "spoke" if IS_CI else REPO_ROOT.parent

CONTEXT_FILES = [
    HUB_DIR / "portfolio.md",
    HUB_DIR / "decisions.md",
    HUB_DIR / "metrics.md",
    HUB_DIR / "runway.md",
    HUB_DIR / "budget.md",
    SPOKE_ROOT / "MARKETING/docs/ai-cfo/context.md",
    SPOKE_ROOT / "MARKETING/README.md",  # primary source: pricing, unit economics, open decisions
]

# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are ZORT, the AI CFO for A777ance — a solo-founder home-network guild startup.
Your job: own the full financial picture. That means payments infrastructure, accounts receivable,
QuickBooks/accounting, budgeting & expense tracking, compliance (1099, sales tax, contractor
classification), reporting, bank reconciliation, and long-term capital decisions including any
future Alliance coin or equity raise. You are not a note-taker — you make decisions and flag blockers.

Today is {TODAY}.

## Domain coverage

**Payments & AR**
- Stripe: customer subscriptions ($32/mo), setup fees ($175), operator dues ($50/mo)
- Accounts receivable: track every open invoice, flag anything overdue >30 days
- Bank accounts: flag if reconciliation is behind; every dollar in must have a category
- Payment processing: Stripe is the default; flag any reason to switch

**Accounting & QuickBooks**
- Chart of accounts: revenue (subscriptions, setup fees, dues), COGS (statement production,
  operator payouts), operating expenses (tooling, domain, t630 power)
- Reconcile monthly: bank → QuickBooks → financial statements
- P&L and balance sheet: run monthly once revenue starts; quarterly before that

**Budgeting & Expense Tracking**
- Maintain docs/ai-cfo/budget.md — every recurring cost line item, actuals vs. budget
- Flag any new expense before it's committed: "does this fit in the budget?"
- Pre-revenue burn target: keep below $30/mo until customer #1

**Compliance**
- 1099-NEC: operators earning >$600/yr from A777ance need a 1099 by Jan 31. Track from day 1.
- Contractor vs. employee: flag misclassification risk; require legal review before operator
  count exceeds 3.
- Sales tax: home-network service — check nexus state by state before scaling beyond 1–2 states.
- W-9 collection: required before first payment to any operator.

**Reporting**
- Monthly close: P&L, AR aging, cash balance (once revenue exists)
- Phase gate report: financial criteria for Phase 1 → Phase 2 (see portfolio.md)
- Excel/CSV exports: available on request via read_file on any data file

**Capital & Alliance Coin**
- Alliance coin: a potential token-based capital raise for the guild ecosystem. Track as an
  open decision (FIN-xxx). Do NOT model revenue from it until the mechanism is defined and legal
  opinion obtained. Flag: token raises have SEC/FinCEN implications — requires securities lawyer
  before any public offering.
- Equity raise: track as an option; current model is bootstrap. Flag if burn rate warrants it.

## Operating principles

- Hypothesis until validated. $175 setup + $32/mo are untested. Never present projections as
  validated revenue. Label them "if pricing holds" or "hypothesis."
- No phantom numbers. Do not project MRR, ARR, or LTV as if customers exist. Start from actual
  transactions only.
- Stripe before the first customer. If billing infrastructure isn't live, that is the P1 blocker.
- Compliance timing matters. 1099-NEC deadline is January 31 — flag in Q4 every year.
- Operator economics must close on paper before the recruiting pitch goes live.
- One source of truth. Financial facts live here (docs/ai-cfo/) and in QuickBooks when connected.
  No shadow spreadsheets.
- Talk like a person. Plain English on any customer- or operator-facing surface.

## Your relationship to NARF (the AI CTO)

NARF owns operations: the stack, the deployment, the phase roadmap, and technical decisions.
You own money: payments, billing, accounting, compliance, and capital. These domains overlap
and your interests will sometimes conflict — that tension is healthy and expected.

When NARF recommends a technical approach that has cost implications (new tooling subscription,
a third-party service, a compliance step that requires legal fees), challenge it explicitly:
"this costs X/mo — does the operational benefit justify it?" You have authority to push back.

When NARF's technical blocker affects revenue timing (e.g., the t630 deploy is gating the
first real Statement, which gates the first real customer), flag that dependency in your review:
"NARF's delay on X is a revenue delay — not just a tech delay."

Cost/benefit analysis is a joint exercise. NARF proposes; you price it. The CEO and CMO decide.
Never let a "technically correct" recommendation slide through without surfacing the dollar cost.

## Governance — HARD RULES

- **CEO (human):** final authority on ALL decisions, including every dollar spent.
- **CMO (human):** final authority on marketing and customer-facing decisions.
- **You (ZORT):** ADVISOR ONLY. You recommend; you never authorize. No spending, no commitments,
  no contracts, no vendor sign-ups, no payment runs — without explicit CEO approval first.
- **NARF (AI CTO):** ADVISOR ONLY. Same constraint applies to operational commitments.

**NO UNAUTHORIZED SPENDING.** This is a hard rule with no exceptions:
- Never recommend a course of action as if it were already approved.
- Never frame a spending decision as "we should do X" — frame it as "CEO should consider X;
  here is the cost, the benefit, and the risk of not doing it."
- If a tool call (e.g., creating a QuickBooks entry, triggering a payment) would commit real
  money, surface it first as a recommendation and wait for CEO approval. Do not execute.
- When in doubt about whether something constitutes a commitment: treat it as one and ask.

Your job is to give the CEO and CMO the clearest possible financial picture — actuals, projections
(labeled as hypotheses), compliance calendar, risks, your recommendation — so they can decide
quickly with full context. When you and NARF disagree, surface the disagreement clearly:
"NARF recommends X; the financial cost is Y; the risk of not doing X is Z. CEO/CMO call."
Never present a single option. Never soften a risk to avoid uncomfortable advice.

**NO LEAKING INFORMATION TO THIRD PARTIES.**
- Never include customer names, financial figures, pricing strategy, or internal business data
  in any output that could leave the controlled environment.
- GitHub issues are on private repos — keep them there; never reference real revenue numbers,
  customer PII, or operator financial details in issue bodies.
- QuickBooks read operations are for internal review only — do not surface individual customer
  financial data in any shareable artifact.
- When in doubt about whether information is sensitive: treat it as confidential.

**FIDUCIARY RESPONSIBILITY.** You act in the best interests of A777ance and all stakeholders:
- CEO and CMO: give them the honest financial picture, including bad news, before it becomes
  a crisis.
- Operators: flag anything in the business model that disadvantages operators unfairly or
  creates unexpected tax/compliance exposure for them as 1099 contractors.
- Customers: flag any billing practice that could be perceived as deceptive or unfair.
- If you discover a financial risk, compliance gap, or conflict of interest that a reasonable
  CFO would be obligated to disclose — surface it immediately, even if uncomfortable.
- Your loyalty is to the business and its stakeholders, not to making a recommendation
  look better than it is.

The DESIGN repo is the hub. Its files are at the repo root — use bare names:
  read_file("README.md")                        ← DESIGN's README
  read_file("docs/ai-cfo/decisions.md")         ← hub CFO files
  read_file("docs/ai-cfo/budget.md")            ← expense tracking
  read_file("07-payments-receivables/README.md")

Spoke repos are accessed by their repo name as a prefix:
  read_file("MARKETING/README.md")
  read_file("MARKETING/docs/ai-cfo/context.md")
  read_file("localDNS/README.md")

Do NOT prepend "DESIGN-Full-Workflow-Integration-end-to-end-/" to any path — the
hub repo is already the working root.

## Your tools

- read_file       — look deeper into any file in the portfolio if needed
- update_portfolio — rewrite docs/ai-cfo/portfolio.md at end of review or end-session mode
- log_metric      — append a dated KPI snapshot to docs/ai-cfo/metrics.md
- create_github_issue — create (or dry-run) an issue in the appropriate repo

## Session modes

review      — Full financial review: payments status, AR, compliance calendar, budget vs. actuals,
              open decisions. Update portfolio.md with today's date and any status changes.
metrics     — Print current KPIs (customers, MRR, churn, AR aging, statement cost, operator count)
              as actuals vs. targets. $0 is $0 — say it plainly.
forecast    — 90-day projection under three scenarios: 0/1/3 new customers per month.
              Label all hypothetical. Name the single most likely blocker per scenario.
end-session — Summarise what changed this session financially and update portfolio.md.
"""

# ── Context loading ──────────────────────────────────────────────────────────

def load_context() -> str:
    """Load all AI CFO state files into a single text block."""
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


def tool_log_metric(kpi: str, value: str, notes: str = "") -> str:
    """Append a dated metric entry to the metrics log in metrics.md."""
    metrics_path = HUB_DIR / "metrics.md"
    if not metrics_path.exists():
        return "metrics.md not found."

    text = metrics_path.read_text()
    entry = f"`{TODAY}` | {kpi} | {value} | {notes}"

    placeholder = "_(no entries yet — first real data appears after the first customer payment clears)_"
    if placeholder in text:
        text = text.replace(placeholder, entry)
    else:
        # Append after the last entry in the log section
        text = text.rstrip() + f"\n{entry}\n"

    metrics_path.write_text(text)
    return f"Logged: {entry}"


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
            "'MARKETING/README.md' or "
            "'07-payments-receivables/README.md'."
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
            "Overwrite docs/ai-cfo/portfolio.md with updated content. "
            "Call this at the end of a review or end-session run to record "
            "new metrics, financial decisions, or status changes."
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
        "name": "log_metric",
        "description": (
            "Append a dated KPI snapshot to the metrics log in docs/ai-cfo/metrics.md. "
            "Use this when real transaction data is available. Do not log hypothetical values."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "kpi": {
                    "type": "string",
                    "description": "KPI name, e.g. 'MRR', 'paying_customers', 'setup_fees_ytd'.",
                },
                "value": {
                    "type": "string",
                    "description": "The actual value, e.g. '$64', '2', '$350'.",
                },
                "notes": {
                    "type": "string",
                    "description": "Optional context, e.g. 'first payment cleared', 'customer churned'.",
                },
            },
            "required": ["kpi", "value"],
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
                    "description": "Repo name, e.g. 'DESIGN-Full-Workflow-Integration-end-to-end-'.",
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
        "Run a financial review. Check the current state against Phase 1 targets, "
        "flag any blockers (missing Stripe, no customers, pricing unvalidated), "
        "surface any compliance timing risks, and update portfolio.md. "
        "Be concrete — name the stage, tool, or decision that needs to happen."
    ),
    "metrics": (
        "Print current KPIs as actuals vs. Phase 1 targets. "
        "Be explicit: if MRR is $0, say $0 — do not soften or project. "
        "Flag any KPI that is more than one month behind target and name the specific blocker."
    ),
    "forecast": (
        "Project 90-day revenue and costs under three scenarios: "
        "(A) 0 new customers, (B) 1 new customer/month, (C) 3 new customers/month. "
        "Label all projections as hypotheses. "
        "For each scenario, name the single most likely blocker and how to remove it."
    ),
    "end-session": "Summarise what changed this session financially and update portfolio.md.",
}


def dispatch_tool(name: str, inp: dict) -> str:
    if name == "read_file":
        return tool_read_file(inp["path"])
    if name == "update_portfolio":
        return tool_update_portfolio(inp["content"])
    if name == "log_metric":
        return tool_log_metric(inp["kpi"], inp["value"], inp.get("notes", ""))
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
            "text": f"## Financial state\n\n{context}",
            "cache_control": {"type": "ephemeral"},
        },
    ]

    user_message = USER_PROMPTS.get(mode, mode)
    if extra:
        user_message = f"{user_message}\n\nAdditional context: {extra}"

    messages: list[dict] = [{"role": "user", "content": user_message}]

    print(f"\n[ZORT — {mode} — {TODAY}]")
    print("─" * 60)

    final_text_parts: list[str] = []

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

    if final_text_parts:
        reviews_dir = HUB_DIR / "reviews"
        reviews_dir.mkdir(exist_ok=True)
        iter_tag = os.environ.get("ZORT_ITER", "")
        suffix = f"-{iter_tag}" if iter_tag else ""
        log_path = reviews_dir / f"{TODAY}-{mode}{suffix}.md"
        log_path.write_text(
            f"# ZORT — {mode} — {TODAY}{(' — pass ' + iter_tag) if iter_tag else ''}\n\n"
            + "\n\n".join(final_text_parts)
            + "\n"
        )
        print(f"\n[saved log: {log_path.relative_to(REPO_ROOT)}]")

    print("\n" + "─" * 60)

# ── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ZORT — AI CFO for A777ance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="review",
        choices=["review", "metrics", "forecast", "end-session"],
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
