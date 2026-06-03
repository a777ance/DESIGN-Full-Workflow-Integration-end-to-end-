# Call scripts & logging discipline

Scripts exist so the human touch is **consistent, not improvised** — and so the calm
voice (00) survives a busy day. They are scaffolding, not a cage: stay human, stay calm,
never alarmist. Every call ends with a write to the CRM (`call_log[]`).

---

## Inbound (someone found us and called)

1. **Warm open:** "Thanks for calling A777ance, this is `NAME`." Match the calm voice.
2. **Listen first:** let them describe the worry in their words. Don't pitch over it.
3. **Reframe to the category:** "What we do is a bit like pest control for your home
   network — we keep the bad stuff out quietly, and every month we send you a simple
   statement that shows what we handled."
4. **One next step:** book the consult in Setmore (03), or confirm an existing one.
5. **Set expectations:** mention the one-time setup fee + the monthly retainer plainly
   (defaults from `MARKETING`, `CHANGE_ME`) — never surprise them at the quote (05).
6. **Log it.**

## Booking-confirmation call/text

- Confirm date/time, address, and who's arriving (named — the trust touch).
- "You'll get a reminder the day before." (SMS, stage 04.)
- Log it.

## Voicemail greeting (brand voice)

> "You've reached A777ance — pest control for your home network. Leave your name, number,
> and your neighborhood, and we'll call you back within `CHANGE_ME` hours. If you'd rather
> just pick a time, the link's on our site."

## Objection quick-reference

| They say | Calm reply (don't over-promise) |
| -------- | ------------------------------- |
| "Isn't this what my ISP's $10 security does?" | "Theirs does a little; ours does meaningfully more and you actually *see* it each month — but we're a person you can call, not a checkbox." |
| "Why the setup fee?" | "It covers the real install on your equipment. We don't discount it because it's real work — but there's no contract trapping you after." |
| "Can't I just buy NextDNS?" | "You could get some of the tech for ~$30/yr. What you can't buy is a vetted local person who patched your TV while you slept. That's the guild." |

## Logging discipline (the non-negotiable)

After **every** call, append to the household's `call_log[]`:

```json
{ "ts": "2026-06-03T16:20:00Z", "dir": "inbound", "by": "NAME",
  "summary": "Worried about kids' tablets; booked consult Thu PM.",
  "next": "Confirm address day-before via SMS" }
```

A call that isn't logged didn't happen, as far as the consult (05) is concerned —
[LAUNCH-NOTES #6](../LAUNCH-NOTES.md#6-call-not-logged-to-the-crm--consult-starts-cold).
