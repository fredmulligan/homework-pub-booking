# Ex6 — Rasa structured half

## Your answer

Ex6 is the part of the agent that says no. Where Ex5 lets the LLM
explore and produce, Ex6 enforces the boring rules that have to hold
no matter what: party of 8 or fewer, deposit of £300 or under.

I think the easiest way to understand why this exists is to imagine
what happens without it. If the only thing standing between a
customer request and a confirmed booking is an LLM, sooner or later
someone says "please, I really need a table for 25, my daughter's
wedding is tomorrow" and the LLM caves. Not because the LLM is
broken, but because LLMs are trained to be helpful. Niceness wins
over rules.

The fix isn't to write a better prompt. It's to take the rules out
of the LLM's hands entirely and put them in code that doesn't get
guilt-tripped. That's what Ex6 is. The structured half receives
the booking data, runs it through a flow that checks the limits,
and returns either a confirmation or a rejection with a reason.
The LLM is not in the loop for that decision.

The implementation is two pieces. The Python side cleans up the
data the LLM produced (£500 as a string, "7:30pm" as a time, party
size as text) and sends it to Rasa over HTTP. The Rasa side runs
the flow, applies the rules, and sends back a structured yes-or-no.
For testing without paying for a Rasa license, we run a tiny mock
HTTP server that returns the same shape of answer, so the rest of
the system doesn't know or care whether it's talking to real Rasa.

The principle generalises beyond pub bookings. Anywhere you mix an
LLM with hard rules (payments, medical doses, security clearances,
legal limits) you want this split. The LLM does the soft part
(understanding the request, talking to the user), and a dumb piece
of code does the hard part (refusing to break the rule). If a
booking goes wrong, you want to know which side of the line it
failed on, and you want the rule side to be small and readable.

## Citations

- starter/rasa_half/validator.py, the data normaliser
- starter/rasa_half/structured_half.py, the HTTP bridge and mock server
- rasa_project/actions/actions.py, the Python that enforces the limits
