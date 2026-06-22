# Process efficiency review — user ↔ AI workflow

*Prepared 2026-06-22 (scheduled routine). Scope: how we run Claude across the seven
A777ance repos — token cost, prompting, and where local LLM / cheaper tiers should carry load.
Current-as-of-today web research folded in; this space moves weekly, so treat the
"keep current" section as the part to re-run, not the conclusions.*

---

## TL;DR — the five things worth doing

1. **Stop reading 6–10 whole files at every session start.** NARF + ZORT together mandate
   ~88 KB (~22K tokens) of *fixed* preamble before a single useful action — every session,
   priced at full input rate. Replace the "read these files" instructions with "read the
   top of these files (newest entry); open the rest only if the task touches them."
   **Biggest single win.**
2. **Exploit prompt caching deliberately.** The CLAUDE.md + portfolio preamble is the
   ideal cache prefix — stable, large, read every run. Cached input is ~90% cheaper. We are
   almost certainly *invalidating* it daily (see §2) and paying full price every time.
3. **Push the daily CTO/CFO reviews to Batch API or a local model.** They are scheduled,
   not latency-sensitive — exactly the 50%-off Batch case, or a job the t630's own LiteLLM
   stack can do for pennies.
4. **De-duplicate the house-style block.** The same ~1,100-word ordering/typography section
   is copy-pasted verbatim into 6 CLAUDE.md files. One canonical copy + a one-line pointer.
5. **Tighten this very prompt** (see §6) — it works, but it's a 9-clause "do everything"
   ask that spends reasoning on breadth.

---

## 1. Where the tokens actually go (measured today)

A session that opens in the DESIGN repo and adopts both the NARF (CTO) and ZORT (CFO)
hats — which the CLAUDE.md explicitly instructs — pays this *before doing any work*:

| Item | Bytes | ~Tokens |
| ---- | ----: | ------: |
| DESIGN `CLAUDE.md` (auto-loaded) | 17,987 | ~4,500 |
| NARF start reads: `portfolio` + `roadmap` + `tech-debt` + `decisions` | 22,183 | ~5,500 |
| ZORT start reads: `portfolio` + `decisions` + `metrics` + `runway` + `budget` + MARKETING `context` | 48,040 | ~12,000 |
| **Fixed preamble per DESIGN session** | **~88,210** | **~22,000** |

`metrics.md` alone is 24.7 KB (~6,200 tokens) and is mandated reading every CFO session.
On top of this, the harness loads **all six** repo CLAUDE.md files into context
(58 KB / ~14.5K tokens total) whether or not the session touches those repos.

So a typical session can begin with **~30K+ tokens of context already spent**, recurring
*every run*. At Opus input pricing ($5/MTok) that's ~$0.15/session of pure preamble; the
daily NARF+ZORT cadence makes it a standing line item, and it grows as `metrics.md` and the
review logs accumulate (there are already 19 daily review files each for CTO and CFO).

This is not an argument to delete the knowledge — it's the right knowledge. It's an
argument to **load it on demand, and cache the stable part.**

---

## 2. Prompt caching — the highest-leverage lever we're probably not pulling

Anthropic prompt caching makes a cached input prefix cost **~10% of normal** (cache read),
for a one-time **~25% write premium**. Industry write-ups this year put well-tuned setups at
**80–95% cache-read rates on static content** and **85–90% cost reduction** on the cached
portion. Our preamble is the textbook candidate: large, stable, re-read every session.

**Why we may be getting ~0% benefit today:** caching is a *prefix match* — any byte change
before the cache breakpoint invalidates everything after it. The known silent invalidators
map directly onto how we work:

- **Per-session dates injected early.** Our reviews and updates are dated (`2026-06-22`);
  if a date or "today" lands in the system/preamble prefix, the cache misses every day.
- **Switching models mid-stream / casually.** Caches are model-scoped. The `/fast` toggle,
  or moving a task between Opus/Sonnet, rebuilds the cache.
- **Reading a different set of files each session.** Variable file order = variable prefix.

**Actions:** keep the stable preamble (CLAUDE.md + the rarely-changing portfolio headers)
*first and byte-identical*; push anything dated or per-run to the *end*; don't switch models
inside a session; verify with `usage.cache_read_input_tokens` (if it's 0 across repeated
runs, an invalidator is live). For the daily routines specifically, consider the **1-hour
cache TTL** so consecutive NARF→ZORT runs in the same window share the warm prefix.

---

## 3. Right-size the model and the channel per job

We run almost everything on Opus. A lot of what these routines do — reading a log, checking
a link, summarizing yesterday's diff, reconciling a number — does not need Opus.

- **Batch API for the scheduled reviews.** The daily CTO/CFO reviews are asynchronous by
  definition. Batch is **50% off input *and* output, no quality penalty**, completes within
  the hour. Caching + Batch **stack** (~95% off the cached, batched portion). This is the
  cleanest dollar win after §1/§2 because it requires no judgment change — just a different
  submission path for the cron jobs.
- **`effort` parameter.** Opus 4.8 supports `low`/`medium`/`high`/`xhigh`/`max`. The
  link-check / doc-integrity / "did anything change" passes are `low`-effort work; reserve
  `high`/`xhigh` for the genuinely analytical reviews. Lower effort = fewer tool calls,
  terser output, real token savings.
- **`max_tokens` discipline.** Don't leave a 64K ceiling on jobs whose answer is a
  paragraph; the model fills space it's given.

---

## 4. Use the local LLM stack we already built

`localDNS` already runs a **LiteLLM router (port 4040) + Open WebUI** on the t630, with a
deliberate reasoning ladder: `local-reason` (deepseek-r1:1.5b on CPU, cool) for light work,
`cloud-gpu-reason` (full R1 on a rented GPU via Tailscale) for heavy, falling over to
`cloud-overflow`. **This is exactly the hybrid architecture the industry is converging on**
in 2026 (LiteLLM gateway + local Ollama tier + Claude as the cloud tier), and the published
numbers are **60–80% cost reduction by routing simple tasks locally and complex ones to the
frontier model.** We have the rails; we're under-using them.

Concretely, route to the local tier the high-volume / low-sensitivity, deterministic-ish
work that doesn't need frontier reasoning:

- doc-integrity / link-checking pre-passes (it's mechanical — `tools/check-docs.py` already
  gates this; the LLM only needs to triage failures),
- first-draft summarization of a day's git diff before a frontier model reviews it,
- classification/extraction (is this commit CTO-relevant? CFO-relevant? both?),
- the "nothing changed → stay silent" gate itself.

Keep on Claude: the actual analytical reviews, anything customer-facing, anything touching
the honesty-of-the-kept-document rule. There's a privacy bonus that fits the house ethos —
PII / customer-roster reasoning *should* stay on the box by default and never hit a cloud
endpoint, which the three-pillar routing model (sensitivity / complexity / availability)
encodes directly.

**Note:** this is tech, not moat — per the repo's own "liquidity before app" rule, spend the
saved time on proof and density, not on gold-plating the router.

---

## 5. Structural cleanups (cheap, compounding)

- **House-style block is duplicated 6×.** The ordering/typography section (~1,100 words) is
  verbatim in every CLAUDE.md. Keep one canonical copy (it could live in DESIGN, the hub)
  and replace the others with a one-line pointer. Saves context on every multi-repo session
  and removes a drift hazard (six copies to keep in sync).
- **Time-based logs grow unbounded.** 19+ daily review files each for CTO and CFO, ~6 KB
  apiece. House style already says "newest first" — extend that to *retention*: keep the
  last N in-tree, archive the rest (a monthly roll-up or a `reviews/archive/`), so nothing
  that globs the reviews dir pulls the full history into context.
- **Make "read X at session start" conditional.** Reword the NARF/ZORT bootstraps from
  "read these 4–6 files" to "read the newest entry / the open-items section; open the full
  file only when the task touches it." Same knowledge, paid for only when used.
- **Consider a SessionStart hook** (Claude Code on the web supports them) to do the cheap,
  deterministic bootstrap (git status, what changed since last run, which hat applies)
  *without* an LLM turn, so the model starts already oriented.

---

## 6. The prompt that launched this run — critique

It works, and the intent is clear. But as written it's a **nine-clause "anything that could
help" ask** ("Locate inefficiencies… reduce token use… better prompting… leverage other
AI… hybrid local+Claude… search the web… best practices… keep up to date… check the
news… and critique this prompt"). That breadth has costs:

- **No success criterion / no priority.** "Anything you could possibly think of" invites an
  exhaustive survey rather than a ranked, decisive answer — which itself burns tokens. A
  frontier model does better with *"give me the top 3–5, ranked by $ saved, with the one
  you'd do first."*
- **Two different jobs in one.** "Analyze our process" (one-shot, do-it-now) and "keep up to
  date / check the news" (recurring, time-based) are different cadences. The second belongs
  in a **scheduled routine** (which this is) with a tight remit, not bolted onto a deep
  one-off.
- **Unscoped.** "Our PROCESS" — which repos, which workflows? Naming the target ("the daily
  NARF/ZORT routines and multi-repo Claude Code sessions") would have saved me the discovery
  pass.

**Tighter rewrite:**

> *"Audit our Claude usage across the A777ance repos for cost. Rank the top 5 fixes by
> dollars saved, and tell me the one to do first and why. Cover: token/preamble cost,
> prompt caching, model/tier selection, and using the t630 LiteLLM stack. Web-check only
> where a 2026 best practice would change the answer. One page."*

Same outcome, a fraction of the wandering. General principle for us: **lead with the
decision you want, cap the length, and name the scope.** Vague "make it better" prompts are
measurably the expensive kind.

---

## 7. Keep-current (re-run this part; it changes weekly)

What's true as of this run, with sources, so the next run can diff against it:

- **Prompt caching:** ~90% off cached input; ~25% (5-min TTL) / 2× (1-hr TTL) write premium;
  80–95% cache-read rates achievable on stable prefixes. *(platform.claude.com prompt-caching
  docs; hidekazu-konishi; mindstudio; knightli.)*
- **Batch API:** 50% off input+output, no quality penalty, ≤1h typical; **stacks** with
  caching for 95%+ off. *(finout.io Anthropic pricing 2026; agentbrisk; devtoollab.)*
- **Hybrid local+cloud routing:** 60–80% cost cut by routing simple→local, complex→frontier;
  LiteLLM-as-gateway + Ollama-local + Claude-cloud is the standard 2026 pattern; route on
  sensitivity / complexity / availability. *(sitepoint hybrid architecture guide 2026;
  mindstudio "run local AI with Claude Code"; litellm auto-routing docs; lushbinary.)*
- **Model lineup today:** Opus 4.8 ($5/$25 per MTok), Sonnet 4.6 ($3/$15), Haiku 4.5
  ($1/$5); Opus 4.8 supports `effort` low→max and 1M context at standard pricing.

**Re-check next run:** new model tiers / price moves; whether Anthropic ships longer cache
TTLs or cheaper batch; LiteLLM routing-policy features. Don't re-derive the structural fixes
above — those are settled until our setup changes.

---

*Method note: token figures are byte/4 estimates for ranking, not billing — confirm any
specific number with `messages.count_tokens` before acting on a dollar figure.*
