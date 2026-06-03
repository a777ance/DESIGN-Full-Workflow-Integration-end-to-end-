# 04 — Phone & comms

**Lives in:** a business line / VoIP (Google Voice / OpenPhone) + SMS.
**Go-live / sync:** set hours, greeting, and routing; log every call to the CRM record.

The human touch a trust business runs on. Every software instinct says automate the
phone away; a guild built on *trust* does the opposite — a real person answering "is this
safe to let into my house?" **is** the product at the moment of highest doubt.

---

## What's here

| File | What it is |
| ---- | ---------- |
| [`call-scripts.md`](call-scripts.md) | Inbound / booking-confirm / voicemail scripts + the logging discipline |

## Small in tooling, large in discipline

| Setting | Value |
| ------- | ----- |
| Business line | `CHANGE_ME` (Google Voice / OpenPhone number) |
| Hours | `CHANGE_ME` — publish them on the GBP (01) and honor them |
| Greeting / voicemail | Brand voice (00); see `call-scripts.md` |
| Routing | To the owning operator for the route (02), else the founders |
| SMS | Appointment reminders + "your Statement is ready" nudges |

## The one rule: log every call to the CRM

Every inbound/outbound call is written to the household record's `call_log[]` so the
consult (05) starts **warm** — no making the prospect repeat what they already said
(corrosive for a trust pitch). See
[LAUNCH-NOTES #6](../LAUNCH-NOTES.md#6-call-not-logged-to-the-crm--consult-starts-cold).
The write-back is an automation (11) where the phone tool supports it, manual where it
doesn't — but it is never skipped.

## Hand-offs

- **← 03 funnels:** booked consults and inbound callers arrive here to be confirmed.
- **→ 08 CRM:** every call appends to `call_log[]` on the record.
- **→ 05 sales:** a confirmed, logged consult is the warm input to the sales conversation.
