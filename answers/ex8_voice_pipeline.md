# Ex8 — Voice pipeline

## Your answer

Ex8 is the bit that lets you actually talk to the agent. You play
the customer, Alasdair MacLeod the pub manager plays himself, a
gruff Scottish landlord whose job is to decide whether to accept
your booking. He's not a script, he's an LLM (Llama-3.3-70B) running
a fairly opinionated system prompt that gives him the persona and
the rules he has to enforce.

There are two modes for talking to him, and they're deliberately
designed so the same code path runs underneath. In text mode you
type and read. In voice mode your microphone audio goes through
Speechmatics for transcription, the manager responds, and Rime.ai
turns his reply back into audio you hear through your speakers.
Either way it's the same persona, the same conversation history,
the same trace events. The transport differs; the brains don't.

The choice that matters most here is graceful degradation. If the
Speechmatics or Rime keys aren't in your environment, the code
doesn't error. It just falls back to text mode with a warning.
That's what lets the grader pass "voice loop implemented" without
needing every student to sign up for two paid APIs. The shape of
the implementation is what gets graded, not whether your mic
worked at submission time.

What I find interesting is that the rules (party of 8 or fewer,
deposit under £300) live entirely in the system prompt. There's
no Python check inside Ex8 saying "if party > 8, reject". The LLM
just refuses in character. That's fine for a demo but it's exactly
why we need Ex6 in the real architecture: a system prompt rule is
soft, an Ex6 validator is hard. In production you'd want both.
Alasdair refuses gracefully on his side, the structured half is
the actual gate.

## Citations

- starter/voice_pipeline/voice_loop.py, run_text_mode + run_voice_mode
- starter/voice_pipeline/manager_persona.py, Alasdair's system prompt
