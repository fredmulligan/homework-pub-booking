# Ex7 — Handoff bridge

## Your answer

Ex7 is the piece that ties Ex5 and Ex6 together. Ex5 is the LLM
that researches a venue. Ex6 is the rule check that approves or
rejects it. Ex7 is the traffic cop that sends the booking from one
to the other and, critically, back again when the first attempt
fails.

The reason this exists is that real bookings aren't one-shot. The
first venue the LLM picks often doesn't work. Maybe it's too small
for the party. Maybe the deposit is too high. In a real-world
booking call you'd expect the agent to say "alright, that one
won't work, let me check another." Ex7 builds that loop. The bridge
runs the LLM, hands the result to the rule check, and if the rules
say no, it sends a new task back to the LLM saying "this got
rejected because X, try something else." The LLM then takes a
second swing.

The other thing Ex7 is doing, less visibly, is producing an audit
trail. Every time the bridge moves a booking from one half to the
other, it writes a trace event. After the conversation ends you
can read the trace and see exactly what was tried, in what order,
and what failed. This matters because when a real booking goes
wrong, you don't want to rerun the conversation to debug it. LLM
calls aren't reproducible. The trace is the only thing left.

The obvious failure mode, and one I think anyone shipping this
would hit fast, is the loop that never terminates. The LLM keeps
suggesting venues that get rejected, the bridge keeps sending them
back, and nobody ever decides "stop, escalate this to a human."
The bridge has a cap on retries (three by default), which is a
blunt fix but the right one. Without it, an unlucky booking could
spend hundreds of pounds in LLM calls and end with nothing.

The general lesson is that any system with two components passing
work between each other needs a guard against infinite ping-pong.
Network protocols solve this with TTL fields. Phone trees solve
it with "press 0 to talk to an operator." Ex7 solves it with the
retry cap. The number isn't sacred; what matters is that you have
one.

## Citations

- starter/handoff_bridge/bridge.py, the round-trip orchestrator
- starter/handoff_bridge/integrity.py, the trace check
