# Ex5 — Edinburgh research loop scenario

## Your answer

The setup is straightforward. Someone wants to book a pub in
Edinburgh, near Haymarket station, for six people on a Saturday.
The agent does the research: picks a venue that fits, looks up the
weather for the night, works out the total cost, and produces a
flyer for the event.

What I think this exercise is actually about isn't "write four
small Python tools." It's about deciding what the LLM is allowed
to invent. The four tools are dumb on purpose. They just read JSON
files and return numbers. The LLM doesn't get to guess the cost,
or improvise the weather, or pick a price out of the air. If a
number ends up in the flyer, it has to have come from a tool.

The smart part of Ex5 is the check that runs after the flyer is
written. It scans the flyer for every concrete fact (every price,
every temperature, every weather word) and asks: did any tool
actually return this value during the run? If the flyer says £560
but the cost tool returned £540, that's flagged. The LLM made up
the £560.

This sounds trivial but it isn't. A human reading the flyer would
not catch it. £560 looks like a fine, plausible number for a pub
booking. The only signal that it's wrong is hidden in the trace.
You'd have to actively cross-reference the logged tool outputs
against the flyer text to spot the gap. The check does that
automatically and refuses to ship a flyer with values it can't
trace.

The pattern is older than LLMs. Banks reconcile transactions the
same way. Accountants tie line items back to receipts. Compilers
verify that variable types match their declarations. Any system
where a creative component produces output needs a verifier that
checks the output against ground truth. LLMs are unusually
creative, so they need an unusually thorough verifier. The
homework's framing of this as "dataflow integrity" is fancy. The
underlying idea is just: trust nothing without a source.

## Citations

- sessions/sess_*/logs/trace.jsonl, the tool call sequence
- sessions/sess_*/workspace/flyer.html, the produced flyer
- starter/edinburgh_research/integrity.py, the verifier
