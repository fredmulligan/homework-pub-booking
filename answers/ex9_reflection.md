# Ex9 — Reflection

## Q1 — Planner handoff decision

### Your answer

The planner is the part of the agent that breaks the user's request
into smaller steps. In my run it produced two: first, go and find
a suitable venue, and second, commit the booking under the rules.
The interesting one is the second. The planner tagged it for the
structured half, meaning "this one's not a creative search, this
one needs rule-checking."

What drove that decision was the language of the subgoal. The
planner is just an LLM looking at a short description and a list
of the available halves. When the description mentions rules,
limits, policy, or anything that sounds like a binary yes-or-no
check, the planner sends it to the structured side. When the
description is about exploring, comparing, or producing content,
it sends it to the loop side.

The thing worth flagging is that this routing is advisory. There's
no enforcement. If the planner mis-labels a subgoal, the
orchestrator will still route it to the half the planner named,
even if that's the wrong place. So the system depends partly on
the planner reading words correctly. That's a soft check.

The lesson I take from that is to not lean too heavily on the
planner's judgement for things that really matter. If a booking
must obey a deposit limit, you don't want that check to live
behind a sentence in a prompt. You want it living in code that
the planner can't bypass even if it wanted to. The planner picks
the lane; the lane decides what happens. Both have to be doing
their job.

### Citation

- sessions/sess_*/logs/trace.jsonl, the planner output
- starter/handoff_bridge/bridge.py, where the assignment becomes a real call

---

## Q2 — Dataflow integrity catch

### Your answer

The fabrication problem looks like this. The cost tool runs and
returns £540 for the booking. The LLM writes the flyer and types
"£560" because some token-level random walk drifted from the real
number. The flyer says £560. To a human reading it, that's a fine
number for a pub booking. Nothing about it screams wrong.

The integrity check catches this not because it understands prices
but because it doesn't trust output. It pulls every number out of
the flyer and asks "did any tool actually return this value?"
£540 came from a tool. £560 didn't. The check refuses to pass
the flyer until every number has a source.

Why a human reviewer misses this: humans check for plausibility,
not provenance. We see a number and ask "does that seem right?"
not "where did this come from?" Most of the time plausibility is
good enough, which is why it's our default. But LLMs are exactly
the case where it fails. They produce plausible-looking nonsense
faster than humans can fact-check, so plausibility is no defence.
You need a check that doesn't care how reasonable the output
looks.

The principle scales. Finance teams reconcile every transaction
against an upstream source. Hospitals double-check every dose
against a chart. The pattern isn't novel; it's old wisdom applied
to a new producer of mistakes. The verifier doesn't need to be
clever. It needs to be stubborn.

### Citation

- sessions/sess_*/workspace/flyer.html, the output being verified
- sessions/sess_*/logs/trace.jsonl, the tool outputs that count as ground truth
- starter/edinburgh_research/integrity.py, the check itself

---

## Q3 — First production failure

### Your answer

If I shipped this to a real pub-booking business next week, the
first thing to break would be the loop that never terminates. The
LLM picks a venue, the rule check rejects it, the bridge sends it
back to the LLM, which picks a similar venue, which gets rejected
the same way. The bridge keeps going. The customer waits. The
Nebius bill grows.

The sovereign-agent primitive that catches this is the retry cap
on the bridge. Three rounds and it gives up. That cap is the
difference between a thirty-pence failed booking and a thirty-quid
one. It's a blunt instrument, but the blunt instrument is the
point. You don't need cleverness here; you need certainty that the
loop ends.

The second primitive that matters once you have the cap is the
trace. When the bridge gives up, the trace is the only record of
what was tried and why each attempt failed. You can't rerun the
conversation to find out, because LLM calls are not reproducible.
The model that returned royal_oak last Tuesday is the model that
might return cafe_royal today. Without the trace you can't debug
a single thing.

Together they make the failure boring. The loop terminates, the
trace explains why. A human picks it up, reads the trace, sees
that the customer asked for a party of forty in a place that caps
at sixteen, and rings them back. That's the system working as
intended. The failure isn't "the agent did something wrong"; the
failure is "the agent admitted it couldn't help and left a clear
record." That's a better failure than most production systems
manage.

### Citation

- starter/handoff_bridge/bridge.py, the round cap
- sessions/sess_*/logs/trace.jsonl, the round-by-round audit trail
