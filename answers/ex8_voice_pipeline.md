# Ex8 — Voice pipeline

## Your answer

Ex8 is the bit where you actually talk to the agent. You play the
customer trying to book a table. The pub manager on the other end
is Alasdair MacLeod, a gruff Scottish landlord with the patience
of a Glasgow taxi driver. He's not a script. He's a Llama model
running a system prompt that gives him a persona and a set of
booking rules to enforce.

There are two ways to talk to him. In text mode you type your
request and read his reply. In voice mode your microphone goes
through Speechmatics to convert your speech to text, the LLM
generates a reply, and Rime turns the reply into audio that plays
back through your speakers. Either way the LLM in the middle is
the same. The transport changes, the brain doesn't.

What makes this worth doing as a homework, I think, is the
graceful-fallback design. The voice mode checks at startup whether
the audio APIs are reachable. If your Speechmatics or Rime keys
aren't set, or your microphone isn't accessible, the code doesn't
crash. It falls back to text mode with a warning. That's the right
default for a system that has to work on a hundred students'
machines with a hundred different microphone configurations.

The thing that struck me building this is how thin the layer between
"voice agent" and "text agent" actually is. The interesting work
sits in the LLM and the system prompt. The voice piece is just an
audio router. Companies that pitch "voice AI" as the differentiator
are mostly selling the wrapper; the intelligence is the model.

The other observation is about where the rules live. In Ex6 the
rules are enforced in Python code. In Ex8 the rules are baked into
Alasdair's system prompt. The two implementations of the same
constraint behave differently under pressure. The Python check is
deterministic: party of 9, rejected, every time. Alasdair will
also reject, but if you push him with a sob story he might
hesitate, soften, or invent an exception. That's exactly why a
real system needs both. Alasdair handles the conversation; the
structured half handles the gate.

## Citations

- starter/voice_pipeline/voice_loop.py, the text and voice modes
- starter/voice_pipeline/manager_persona.py, Alasdair's system prompt
