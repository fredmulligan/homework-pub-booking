# Ex6 — Rasa structured half

## Your answer

Ex6 builds the part of the agent that says no to bad bookings.
Where Ex5 lets the LLM be creative (find me a pub), Ex6 enforces
hard rules in Python code: max party size 8, max deposit £300.

The flow is simple. The loop half finishes researching and hands
over messy booking data — things like "£500" as a string, "7:30pm"
as a time, party size as text. My code cleans that up into something
Rasa understands (numbers, ISO dates, 24h times), POSTs it to a
Rasa webhook, waits for a yes or no, and turns the reply back into
a result the rest of the system can use.

The interesting bit is the mock setup. A real Rasa container needs
a paid license and ~400MB of install — too much friction for daily
testing. Offline mode spins up a tiny Python HTTP server that
pretends to be Rasa: same response shape, same accept/reject logic,
no Rasa actually running. Lets you iterate on the Python side
without standing up the whole dialog stack.

Three things I had to think about:

- The validator throws when input is broken beyond repair. My code
  catches it and returns a failure result instead of crashing —
  whatever calls me expects a result object either way.
- Network errors get a specific error code so the caller can decide
  whether to retry. I don't retry on my own.
- Each booking gets a stable ID that's just a hash of venue + date +
  time. If the same booking gets retried, Rasa sees one conversation,
  not two. Saves you weird state bugs.

## Citations

- starter/rasa_half/validator.py — normalise_booking_payload + helpers
- starter/rasa_half/structured_half.py — RasaStructuredHalf.run + mock server
