# Email & text — the copy, ready to send

A trust business can't afford to feel like spam. The list is built **off the customer list
(08)**, everyone on it asked to be there, and we never buy or scrape addresses. It lives in
Mailchimp (or similar); the customer list is the truth, the email tool just sends.

Below is the actual copy — paste it, swap the `[brackets]`, send it.

---

## Who gets what

| List | Who's on it | What they get |
| ---- | ----------- | ------------- |
| **Leads** | Asked about us, haven't bought yet | A short nurture — the problem, a real statement, one button |
| **Customers** | Paying, active | The monthly "your statement's ready" note + the occasional tip |
| **Curious about operating** | Tapped "Connect in the Alliance" on a statement (09) | The "you could do this too" sequence |
| **Gone quiet** | No activity in 90 days | One gentle nudge, then we stop |

These lists are pulled automatically from the customer list — nobody maintains them by hand.

## Lead nurture — 3 emails

**Email 1 — the problem (send on signup)**

> **Subject:** What's on your Wi-Fi is talking behind your back
>
> Hi [first name],
>
> Quick thing. Count what's on your home Wi-Fi — TVs, phones, the doorbell, the kids'
> tablets. Probably 15 or 20 things. All of them chat with the internet all day, and a lot
> of what they say is junk: trackers, ads following you around, your TV reporting what you
> watch.
>
> None of it's a crisis. It's just nobody's watching it. We do — quietly, for every device,
> with a real local person behind it. Here's a one-page example of what that looks like in a
> month: **[link to a live statement]**
>
> — [your name], A777ance

**Email 2 — the proof (2 days later)**

> **Subject:** Three things happened to this home last month. They felt none of them.
>
> That line is from a real customer's statement. Scroll it on your phone — scan the little
> code, or just tap: **[link to the live gallery]**. The fixes are signed by name, because a
> real person did them.
>
> Want us to take a free look at your setup? Pick a time that works: **[booking link]**

**Email 3 — the human + the ask (4 days later)**

> **Subject:** Why a person beats an app for this
>
> You can buy some of the tech for thirty bucks a year. What you can't buy is a
> background-checked, bonded neighbor who patched your TV while you slept and put their name
> on it. That's the whole idea.
>
> No contract, cancel anytime, setup's a one-time $175 and it's $32/month after. Grab a free
> look here: **[booking link]**

## Customer — monthly statement note

> **Subject:** Your [month] statement is ready 📄
>
> Hi [first name] — your A777ance statement for [month] is ready. Here's the quiet we kept
> this month: **[link to the online statement]**
>
> Happy with us? The nicest thing you can do is tell the neighbor next door — here's a link
> they can use, and it helps your whole block: **[referral link]**
>
> — [operator name]

## Text messages (short, human)

- **Appointment reminder:** "Hi [name], it's [operator] with A777ance — confirming I'll be by
  tomorrow around [time] to set up your box. Reply C to confirm or R to reschedule."
- **Statement ready:** "Your A777ance statement for [month] is up: [short link]. Quiet month
  — that's the goal. — [operator]"
- **Gentle dunning (07):** "Hi [name], looks like your card didn't go through this month — no
  worries, here's a quick link to fix it: [link]. — A777ance"

## The consent rule (non-negotiable)

Every contact carries, on their record: their `email`, whether they opted in (`consent`,
never a pre-checked box), where they opted in (`consent_source`), and when (`consent_ts`). If
they unsubscribe, we stamp `unsubscribed_ts` and never mail them again. **No consent record →
we don't email them.** ([LAUNCH-NOTES #5](../LAUNCH-NOTES.md#5-email-list-collected-without-consent-record).)

## Keeping it clean

- One-click unsubscribe on every send, honored instantly.
- Real mailing address in the footer, honest subject lines (CAN-SPAM basics).
- No invented stats, ever, and never fear-bait — same honesty rule as the statement.
- If bounces or complaints creep up, pause and clean the list before the next send.

## Hand-offs

- **← 08 customer list:** the source of truth for every address, consent flag, and list.
- **→ 03 / 06 / 09:** the buttons send people to the booking form, the live statement, and
  the operator funnel.
