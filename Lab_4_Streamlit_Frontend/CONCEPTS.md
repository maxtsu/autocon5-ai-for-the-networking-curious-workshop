# Lab 4 Concepts: Streamlit Frontend

> 10-15 min introduction before hands-on starts.

## The big picture

Three labs in, you've built an actual AI-augmented engineering tool. It works. It's accurate. It's reasonable.

It also lives in a Python script that only you can run.

That's not a tool — it's a prototype. To become a real product (even a small one), it needs a face. Someone on your team who isn't comfortable in a terminal needs to be able to use what you built, get answers, screenshot output for a Slack channel. That's what Lab 4 builds — a chat web UI that wraps the Lab 3 agent.

The agent code from Lab 3 doesn't change. You're not rebuilding intelligence; you're putting a face on it.

## Why a UI is the unlock

This isn't just a polish step. It's the moment a tool stops being yours and starts being your team's.

Real story: every network team has someone like Maria who reads configs fluently but doesn't write Python. Every team has someone like Raj who lives in vim. If your AI co-pilot only runs from `python agent.py`, you've built Raj a toy. Maria can't use it. Maria isn't going to use it.

A chat UI levels that playing field. Raj can still run the Python script. Maria gets the same intelligence through a chat window. That's how AI-augmented engineering goes from "interesting demo" to "actual practice change."

## What Streamlit is

Streamlit is a Python library for building web UIs from regular Python scripts. No HTML. No JavaScript. No CSS. You write:

```python
import streamlit as st

name = st.text_input("Your name?")
if name:
    st.write(f"Hello, {name}!")
```

…and you have a web app. Streamlit handles rendering, routing, state.

The trick that makes Streamlit feel weird the first time: **every interaction reruns your entire script from the top.** Click a button → script reruns top-to-bottom. Type in a text box → same thing. Sounds wasteful, but it makes the mental model dead simple — your UI is always a pure function of current state.

Once you've internalized "interactions cause reruns," everything else clicks. State that needs to persist across reruns goes in `st.session_state`. Expensive setup (like building a LangChain agent) goes in `@st.cache_resource`. Everything else just renders fresh each time.

## What you'll have built by the end

```
   ┌──────────────────────────────────────────────┐
   │   Streamlit chat UI         (Lab 4)          │
   │   - st.chat_input                            │
   │   - st.chat_message                          │
   │   - st.session_state for history             │
   └─────────────────┬────────────────────────────┘
                     │ "What's BGP on r1?"
                     ▼
   ┌──────────────────────────────────────────────┐
   │   LangChain agent           (Lab 3)          │
   │   - decides which tool to call               │
   │   - reasons over tool outputs                │
   └─────────────────┬────────────────────────────┘
                     │ get_bgp_state(node='r1')
                     ▼
   ┌──────────────────────────────────────────────┐
   │   BGP tool                  (Lab 3 + Lab 2)  │
   │   - reads BGP output                         │
   │   - parses with Pydantic schema              │
   │   - returns structured neighbors             │
   └─────────────────┬────────────────────────────┘
                     │ raw text
                     ▼
   ┌──────────────────────────────────────────────┐
   │   Sample data / live containerlab            │
   └──────────────────────────────────────────────┘
```

The full stack, bottom to top:

- **Data**       — canned files in this lab, live containerlab in production
- **Parsing**    — Lab 2's analyzer, Pydantic-validated extraction
- **Tool**       — Lab 3, parser wrapped as an agent-callable function
- **Agent**      — Lab 3, reasons over questions and tool calls
- **UI**         — Lab 4, chat interface anyone can use

Roughly 140 lines of Python across all four pieces. Build the stack once, swap any layer independently.

## The "config generator" alternative

In Going Further, you'll see an alternative app pattern — the **config generator** with human-in-the-loop review. Same Streamlit primitives, different problem: user types natural-language intent ("add a BGP neighbor"), the LLM generates SR Linux config, the user reviews and approves before anything touches a device.

This is the talk's "human-in-the-loop guardrail" pattern made tangible. The "approve" button in the demo does nothing destructive — that's deliberate. The human is the safety gate. Production versions push to the device on approve; this demo deliberately stops short of that, because the safety message lands harder when you can see exactly where the gate would be.

## Where this fits in the workshop arc

Lab 4 is the workshop's payoff. Whatever else you remember from today, you'll remember the moment you typed a question into a chat box and watched your own tooling answer it.

After Lab 4, the only thing left is bonus discussion — where this all goes from here. MCP. Real RAG with vector stores. Evals (automated tests of your agent's accuracy). Production deployment patterns. Lab 4 plants the flag; the bonus material points at where you'd plant the next one.
