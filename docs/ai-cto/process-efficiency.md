# Process efficiency — human↔AI workflow & token economics

A review of how we use Claude (and AI generally) across the A777ance repos, with
concrete ways to cut token spend and improve results. Time-based items newest-first.

_Last reviewed: 2026-06-20._

---

## TL;DR — the five that matter

1. **Our `CLAUDE.md` files are the single biggest controllable cost.** They load on
   every turn of every session. We carry ~14.6k tokens of `CLAUDE.md` across repos
   (localDNS 5.1k + DESIGN 4.5k + MARKETING 2.7k + others). Industry target for a
   `CLAUDE.md` is **under ~500 tokens**; ours are 5–10× that. **Biggest single win.**
2. **The "read these 4–6 files at session start" instructions multiply that.** DESIGN's
   §5/§6 tell the agent to open portfolio/roadmap/tech-debt/decisions + two CFO files
   before doing anything. That's another ~several-thousand tokens spent before work
   begins, often on files irrelevant to the task.
3. **We already own a hybrid stack and barely use it.** The t630 runs LiteLLM + Ollama
   + Open WebUI + a cloud-GPU reasoning tier. Routing the routine 60–70% of tasks
   (classification, extraction, formatting, draft statements) to local models is a
   proven **60–80% cost cut**. Today everything goes to Claude.
4. **Prompt caching is the highest-ROI lever and is mostly automatic** — but only pays
   off if the stable stuff (CLAUDE.md, system context) sits at the *front* and doesn't
   churn. Cache hits cost ~0.1× of normal input. Keep the prefix stable.
5. **Scope each session to one repo.** Open Claude Code in the specific repo, not a
   parent dir that pulls in all seven `CLAUDE.md` files. Start fresh sessions per task;
   `/compact` early (threshold ~70, not the default ~95).

---

## A. The `CLAUDE.md` problem, with our numbers

Measured 2026-06-20 (`wc -c`, ÷4 for rough tokens):

| Repo | CLAUDE.md | README.md |
| ---- | --------- | --------- |
| localDNS | ~5,118 tok | ~16,795 tok |
| DESIGN | ~4,496 tok | ~3,482 tok |
| MARKETING | ~2,665 tok | ~3,702 tok |
| customers | ~1,033 tok | ~891 tok |
| claude-code-homelab | ~724 tok | ~510 tok |
| Azure-lab | ~573 tok | ~9 tok |

A `CLAUDE.md` is loaded **before** Claude reads any code or your task, and stays
resident for every message. A 5k-token file is a 5k-token tax on every single turn.

**What to do:**
- **Cut each `CLAUDE.md` to a lean core** (target <1k tokens; <500 is the gold
  standard). Keep: what the repo is, the hard rules (push-to-main, secrets, honesty
  rule), and pointers. Move everything else into linked docs the agent reads *only when
  the task needs it*.
- The big tables (deploy-path map, stage map, known-issues) are reference material, not
  per-turn context. Split them into `docs/deploy-paths.md`, `docs/known-issues.md`, etc.,
  and link from `CLAUDE.md`. The house-style block (~repeated verbatim in all 7 files)
  could live once in a shared, linked `STYLE.md` instead of being duplicated everywhere.
- **De-duplicate the house-style section.** It is copy-pasted, near-identical, into all
  seven repos. That's ~5–6k tokens of the same text we re-load constantly. One canonical
  copy, linked.
- Soften the §5/§6 "read these files at session start" mandates to "read X *if the task
  touches* portfolio/finance/roadmap." Unconditional reads are the expensive part.

> There's an open Anthropic feature request (#33464) for native compression of
> instruction files — worth tracking, but don't wait on it; trimming is available today.

## B. Use the hybrid stack we already built

The homelab already has the routing layer (LiteLLM on :4040, Ollama models, Open WebUI,
the `cloud-gpu-reason` tier on a rented GPU). The standard 2026 pattern is an
intelligent router that picks local vs. cloud by **task complexity, data sensitivity,
and availability**. We have the pieces; we just need to point work at them.

Route to **local (free, private)**:
- Drafting/rewriting statement copy and "Handled For You" entries (then a Claude pass to
  polish the final kept document).
- Classifying/extracting from the roster, log summarization, commit-message drafts.
- Anything touching **real customer data** in the `customers` repo — privacy win *and*
  cost win, since that data shouldn't leave the box anyway.

Route to **Claude (cloud)**:
- Cross-repo reasoning, architecture/ADR decisions, the final pass on anything that
  ships for money or to a customer, security-sensitive review.

This doubles as a privacy control: sensitive lookups already stay on-box per the DNS
design philosophy — apply the same instinct to LLM calls on customer data.

## C. Token-economics context (2026, moves fast)

- **June 15, 2026 billing change → paused.** Anthropic announced splitting programmatic
  (Agent SDK / GitHub Actions / third-party) usage onto a separate dollar-metered credit
  at API rates, then **paused it** before it took effect. Subscription agent use
  continues as before for now — meaning agentic use is still effectively subsidized vs.
  raw API. **Don't architect around the paused plan, but assume metering returns.**
  Building the habits in this doc now is insurance.
- **Prompt caching:** cache hits ≈ 0.1× input cost; the highest-ROI optimization for
  repetitive agentic workloads. Keep the stable prefix stable.
- **Skills vs. MCP vs. subagents cost very differently:** a skill costs ~30–50 tokens
  until invoked (body loads ~up to 5k only when used); a multi-server MCP setup can cost
  **50k+ tokens upfront**; subagent-heavy runs can use ~7× a single-thread session.
  Rule of thumb: **many cheap skills, few MCP servers, subagents only to keep noisy
  research/review out of the main context.**

## D. Better prompting (cheaper *and* better output)

- **One repo, one task, fresh session.** Don't let one long session sprawl across repos
  and topics — "dark context" (stale tokens) accrues and you pay for it every turn.
- **Compact early** (`/compact`, threshold ~70). Or end the session and start clean.
- **Ask for terse output when you don't need prose.** A standing "be terse / no preamble"
  instruction cuts output tokens materially on heavy workflows.
- **Use XML-ish structure for non-trivial asks:** `<context>`, `<task>`, `<constraints>`.
  Separating data from instruction reduces misfires (and re-runs are pure waste).
- **Watch tool output, not just your prompts** — tool/command output is usually the
  silent majority of token spend and compounds every turn. Prefer scoped reads over
  dumping whole files.

## E. On the prompt that requested this review

The originating ask ("locate inefficiencies… is there a better way… ANYTHING that could
help… search the web… check the news… keep up to date") is itself a small case study:

- **It's open-ended and unbounded.** "ANYTHING" invites a broad, expensive sweep with no
  success criterion. Broad is fine for a kickoff, but it costs more and risks drift.
- **It bundles many sub-questions** (token use, prompting, hybrid local LLM, news) into
  one turn — each would get a sharper answer scoped on its own.
- **A tighter version:** _"Audit our CLAUDE.md token cost across repos and propose cuts to
  get each under 1k tokens. Separately, draft a local-vs-Claude routing rule for our
  LiteLLM stack. Cite 2026 sources."_ — bounded, has a finish line, splits cleanly.
- **For recurring scans** ("keep up to date, check the news day by day"), this belongs in
  a scheduled routine with a *narrow* trigger ("notify only if Anthropic pricing/limits
  change"), not a broad re-run — otherwise it spends tokens to tell you nothing changed.

## Sources

- Anthropic June 2026 billing change & pause — codersera, digitalapplied, InfoWorld, Computing
- CLAUDE.md / token optimization — buildtolaunch (Stop the $1,600 Bill), firecrawl (12 Ways),
  Anthropic Claude Code cost docs, GitHub issue #33464
- Hybrid local/cloud routing — sitepoint (Architecture Guide 2026), buildmvpfast, kunalganglani benchmark
- Skills/MCP/subagents overhead — codersera practitioner guide, systemprompt.io, alexop.dev
- General token tips — analyticsvidhya (23 Tips), apexhours (Token Optimizer's Manifesto)
