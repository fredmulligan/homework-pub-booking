# Ex9 — Reflection

## Q1 — Planner handoff decision

### Your answer

In my Ex7 run, the planner produced two subgoals. The first was
about researching venues (assigned to the loop half, where the LLM
gets to be creative). The second was about actually committing the
booking under the agreed rules (assigned to the structured half).
That second assignment is the interesting one. It's the moment the
planner decides "this is not a creative task, this is a rule-following
task, send it to the deterministic side."

The signal that drove the decision was the language of the subgoal
itself. The planner is just an LLM with a list of the available
halves and a one-line description of what each does. When a
subgoal description includes words like "rules", "policy", "limits",
or "commit", the planner naturally routes it to the structured
half. When the description is about searching, comparing, or
producing content, it routes to loop.

What's worth flagging is that this routing decision is advisory,
not enforced. The planner can put the wrong tag on a subgoal and
the orchestrator will still run it through the half the planner
named. There's no automatic check that says "wait, that subgoal
needs Python rules, not an LLM." If the structured half didn't
exist at all, a subgoal marked "structured" would just be dropped
on the floor. So in practice you don't want to lean too hard on
the planner's judgement. The harder rules live in the structured
half's Python (Ex6), where prose ambiguity can't reach them.

### Citation

- sessions/sess_*/logs/trace.jsonl, planner output and the
  subgoal-to-half assignments
- starter/handoff_bridge/bridge.py, where the assignment is
  consumed and turned into actual calls

---

## Q2 — Dataflow integrity catch

### Your answer

The scenario the dataflow integrity check is designed for is the
one where the LLM produces a flyer with numbers that look fine
but didn't actually come from a tool. Imagine the calculate_cost
tool returns £540, but when the LLM writes the flyer it types
"£560". Close enough to look right, plausible in context, and
nobody reading the flyer would think to cross-reference it against
the calculation.

verify_dataflow catches this because it ignores plausibility and
only looks at provenance. It pulls every concrete fact out of the
flyer (every price, every temperature, every weather condition)
and asks "did any tool actually return this value during the run?"
If the answer is no, the flyer fails the integrity check and the
run is reported as broken.

A human reviewer would not catch this in casual review. £560 looks
like a fine number for a pub booking. The only signal that it's
wrong is that the trace shows the cost tool returned £540, and you
have to actively cross-reference to see the gap. The integrity
check does that cross-reference automatically. The generalisable
lesson: whenever the LLM is restating numbers it received from a
tool, you want a mechanical audit that ties the restated value
back to its source. Vibes-based review of LLM output doesn't scale.

A good way to test this in your own run: change one constant in
the flyer template to a deliberately wrong value (say, multiply
the total by 1.04), re-run, and confirm verify_dataflow flags it.
That's the proof your check actually works.

### Citation

- sessions/sess_*/workspace/flyer.html, the produced flyer
- sessions/sess_*/logs/trace.jsonl, the tool call sequence that
  the integrity check compares against
- starter/edinburgh_research/integrity.py, the verifier itself

---

## Q3 — First production failure

### Your answer

If you shipped this to a real pub-booking business next week, the
first failure you'd hit is the bridge loop never terminating. The
loop half suggests a venue, the structured half rejects (party too
big, deposit too high, whatever), the bridge sends it back to the
loop, and the loop suggests the same venue again. Or one that also
fails. Burning Nebius tokens on every round, no progress, the
customer waiting on the phone.

The primitive that surfaces this is the bridge's max_rounds cap.
It's a blunt instrument (three retries and we give up) but it's
the difference between "spent £0.30 and gave the customer a clean
escalation" and "spent £80 trying to autonomously book a wedding
for forty." In production you'd want the cap, plus a clear
escalation path: at round N+1, hand off to a human, with the trace
attached so the human knows what was tried.

The other primitive that helps here is the trace itself. When the
bridge gives up, the trace has every round_start, every state_changed,
every venue tried and every rejection reason. That's how you debug
"why did this customer never get a booking?" without rerunning the
whole conversation. Production agents need a trace this explicit
because LLM behaviour isn't reproducible by replay. You can't rerun
last Tuesday's conversation and expect the same tool calls.

So: failure is infinite-loop / runaway cost. The surfacing primitive
is the round cap on the bridge. The debugging primitive is the
session trace. Both are non-negotiable for shipping.

### Citation

- starter/handoff_bridge/bridge.py, the max_rounds cap
- sessions/sess_*/logs/trace.jsonl, the round_start /
  state_changed events that make a stuck loop visible
