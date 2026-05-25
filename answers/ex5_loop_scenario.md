# Ex5 — Edinburgh research loop scenario

## Your answer

Ex5 is the open-ended research half of the agent. The setup: someone
wants to book an Edinburgh pub for 6 people on a Saturday near
Haymarket. The agent has to figure out which pub, what the weather
will be, how much it'll cost, and produce a flyer for the event.

The point of this exercise isn't really the booking — it's the
discipline around how an LLM should call tools. The agent has four
of them: search venues, look up weather, calculate cost, generate
the flyer. Three of those are pure reads from local JSON. One writes
a file. The framework flags the reads as parallel-safe and the write
as not, so the executor batches the reads into a single turn and
runs the flyer write on its own afterwards. It's a small detail but
it saves you from the kind of race condition where two tools both
think they're writing the canonical flyer at the same time.

The bit I find most useful in this whole exercise is the dataflow
integrity check. After the flyer is written, a separate function
reads every concrete fact in it — every price, temperature, weather
condition — and checks that the same value actually came back from
a real tool call earlier. If the flyer says "£540 total" but no
tool ever returned 540, that's flagged as a fabrication. The LLM
made it up.

This catches a class of failure that human review misses. A flyer
that says "£560" looks fine, because £560 is a perfectly reasonable
price. You'd only notice it was wrong if you cross-referenced the
trace and saw the cost tool actually returned £540. The integrity
check does that cross-reference automatically and refuses to ship
a flyer with numbers no tool produced. The lesson generalises: any
time the LLM has to summarise or restate facts in a user-facing
output, you want a mechanical audit that ties output values back
to tool outputs.

## Citations

- sessions/sess_*/logs/trace.jsonl — tool call sequence
- sessions/sess_*/workspace/flyer.html — the produced flyer
