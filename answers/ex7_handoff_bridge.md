# Ex7 — Handoff bridge

## Your answer

Ex7 is the orchestrator that shuttles control between the two halves
of the agent. The loop half does free-form research, the structured
half enforces rules. The bridge sits between them and runs the
round trip: loop runs, hands off to structured, structured either
accepts or rejects, and on rejection the bridge sends it back to the
loop with the rejection reason so it can try something else.

The interesting bit is the reverse path. When the structured half
rejects a booking (say, party of 12 won't fit in haymarket_tap's 8
seats), the bridge doesn't just give up. It rewrites the task to
include the prior result and the rejection reason, then sends it
back to the loop. In a real LLM setting the loop would read "this
got rejected because of party_too_large" and search for a bigger
venue. In the offline test we cheat: the next pick is hardcoded to
royal_oak (16 seats) so the test is deterministic.

Every transition emits a trace event so you can see what happened
afterwards. The integrity check reads the trace and complains if
the bridge claims success without actually doing the rounds. That
catches the obvious failure mode where someone short-circuits the
bridge and reports victory.

One small piece of bookkeeping: old handoff files get moved to a
logs/handoffs/ folder instead of deleted. The grader cares about
this because it lets you reconstruct what happened during a session
review, which is useful when something went wrong and you're
looking at it the next day.

Worth flagging the obvious risk: this thing can loop forever if no
venue ever satisfies the rules. The bridge caps it with max_rounds
(3 by default), which is a blunt fix but the right one for now.

## Citations

- starter/handoff_bridge/bridge.py, HandoffBridge.run + helpers
- starter/handoff_bridge/integrity.py, verify_dataflow
