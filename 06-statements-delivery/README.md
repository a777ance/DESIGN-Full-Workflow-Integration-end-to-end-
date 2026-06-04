# 06 — Statements delivery

**Lives in:** the `localDNS` statement tool + email + print/mail + the QR codes.
**Go-live:** run the monthly job; email and mail the statements; the QR codes are live.

**This is the center — the thing everyone pays for.** And the most important rule of this
whole stage: **we don't build or rewrite the statement here.** The statement is the
gold-standard artifact, built and published over in `localDNS`. This stage is the *delivery
routine* around it: run the monthly job, write the human notes that make it personal, send
it, and stop there.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`monthly-run.md`](monthly-run.md) | The monthly checklist + how to write the "Handled For You" notes |

## The two statements

| Statement | Who it's for | Where it's built |
| --------- | ------------ | ---------------- |
| **Network Activity Statement** | The homeowner — a one-page monthly proof, the "sticker on the door" | `localDNS/docs/statements/client/` |
| **Alliance Member Portfolio** | The operator — one view across their whole book of homes | `localDNS/docs/statements/operator/` |

What's actually on each one (the account summary, the "Handled For You" log, the traffic
donut, "How You Compare," the "Connect in the Alliance" card, the QR codes) is documented and
built in `localDNS` — read it there; we don't restate it here.

## Why we deliver instead of rebuild

The statement is the gold standard precisely *because* it has one home (`localDNS`), is built
the same way every time, and is honest about which numbers are real. If we started hand-editing
copies here, we'd have two versions that drift apart — and we'd risk printing a stale or
made-up figure on a document people keep ([LAUNCH-NOTES #8](../LAUNCH-NOTES.md#8-statement-forkededited-in-this-repo-instead-of-generated-from-localdns)).
So we feed the tool good inputs and let it do the rendering.

## The monthly run, in plain steps

```
1. refresh each box's numbers      localDNS does this — the real measured stuff
2. write the human notes           ← this stage's real job: the "Handled For You" log
3. build the statements            localDNS does this from the numbers + your notes
4. skip anyone who hasn't paid (07) ← never give the proof away for free
5. send it                         email + mailed paper + the QR codes
```

Steps 1 and 3 are `localDNS`'s job — you just run them. Steps 2, 4, and 5 are this stage's.
The checklist and the note-writing guide are in [`monthly-run.md`](monthly-run.md).

## The human notes — the part that makes it personal

The one thing this stage genuinely *writes* each month is the **"Handled For You" log**: the
real work done, in plain language, **signed by name**. This is where the human shows up in the
artifact:

> *"Your living-room smart-TV hung on a bad connection; it was cleared remotely at 11:40pm."*
> — Fixed in your home by Jose · while you slept

Keep it in the calm voice (00) — *your home, your TV* — never generic tech-speak. And if
nothing happened, say exactly that: *"nothing to change this month, beautifully boring."* Never
invent work to fill the page.

## The honesty rule (carried over from localDNS)

Some numbers are real and measured today (how many lookups, how much got blocked, uptime). Some
aren't built yet (a breakdown by category in gigabytes; how you compare to the neighbors). **Don't
put a number on the statement that the box didn't actually measure**
([LAUNCH-NOTES #10](../LAUNCH-NOTES.md#10-statement-prints-figures-the-box-did-not-measure)). When
in doubt, leave it off. A document people keep has to be true.

## Hand-offs

- **← 05/08:** the set-up, paid customers on the list are who the run is for.
- **← 07 payments:** the paid / not-paid check that decides who gets a statement this month.
- **→ 09 recruiting:** a "Connect in the Alliance" tap turns into an operator lead.
- **→ 02 email:** the "your statement's ready" send, and the refer-a-neighbor ask inside it.
