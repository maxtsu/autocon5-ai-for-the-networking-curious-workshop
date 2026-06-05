# Lab 3 Concepts: Building a Network Agent

> 10-15 min introduction before hands-on starts.

## The big picture

So far in the workshop, every LLM call has been a single round-trip: you send a prompt, you get back text. You parse the text, you do something with it, you might send another prompt. The flow is hand-coded by you.

An **agent** flips this on its head. Instead of you orchestrating each call, the LLM orchestrates its own calls — deciding when to fetch data, which tool to use, when to ask a follow-up of itself, and when to stop and answer.

That sounds magical. It's not. The mechanism is straightforward, and you're going to build one in 25 minutes.

## What an agent actually is

An agent is a **loop**. Here's the loop:

```
                  ┌─────────────────────────────┐
                  │       User's question       │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │  Think                      │
                  │  "Which tool, if any?"      │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │  Act                        │
                  │  Call the tool              │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │  Observe                    │
                  │  Read the tool's output     │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │  Done?                      │──── No ──┐
                  └──────────────┬──────────────┘          │
                                 │ Yes                     │
                                 ▼                         │
                  ┌─────────────────────────────┐          │
                  │       Final answer          │          │
                  └─────────────────────────────┘          │
                                                           │
                  (loop back to Think with the observation)│
                                                           │
                  ◄────────────────────────────────────────┘
```

Three things to notice:

1. **The LLM decides what to do, not you.** You hand it a question and tool descriptions. The LLM decides to call a tool (or not). You hand it the tool's output. The LLM decides whether to call another tool or write the final answer.
2. **The loop can have multiple cycles.** "Compare BGP between r1 and r3" → agent calls the tool for r1, observes, calls it for r3, observes, then synthesizes. Two tool calls + one final answer.
3. **An agent with no tools is just an LLM.** An agent with bad tools is a bad LLM. Tool design — names, docstrings, parameter shapes — is where most of the agent's quality comes from.

## What "tools" really are

A "tool" in this world is just a Python function with a clear signature. LangChain's `@tool` decorator reads the function's signature and docstring, then describes the tool to the LLM as part of the system prompt. The model sees something like:

> *"You have access to a tool named `get_bgp_state(node: str) -> str`. The docstring says: 'Get the BGP peering state for a node. Use this tool when the user asks about BGP neighbors, peering status, or session state on a specific router.'"*

That's the entire mechanism. The LLM is reading function descriptions and deciding "yes, this question matches that tool's description, let me call it."

**Therefore: writing good docstrings is the most important agent engineering you'll do.** A vague docstring → a confused agent. A precise docstring → an agent that calls the right tool with the right arguments.

In the lab you'll see this directly. The `get_bgp_state` tool's docstring includes "Use this tool when the user asks about BGP neighbors..." and "Args: node — one of 'r1', 'r2', 'r3'." The agent uses that text to extract the node name from natural-language questions.

## Why "agent with one tool" is still meaningful

If you give an agent only one tool, isn't that just a function-call wrapper? Almost — but not quite. The agent still decides:

- **Whether to call it at all.** "What is BGP?" doesn't need the tool. "What's BGP on r1?" does. The agent decides.
- **What arguments to use.** "How's r1 doing?" → call with `node='r1'`. "Check the second router" → call with `node='r2'`. The agent parses intent.
- **How to interpret the result.** The tool returns structured text. The agent reads it and frames an answer in the user's language.

Even with one tool, you have an entity that maps natural-language questions → function calls → natural-language responses. That's a real product.

Going Further adds more tools (OSPF, interfaces, diagnose) and that's when multi-step reasoning kicks in — but the core concept is the same.

## A note on small models and tool calling

Step 5 of the lab is going to fail or struggle, by design. You'll swap the OpenAI model for our local `llama3.2:3b`, re-run the same agent, and watch it not work as well.

That's worth noticing carefully. Tool calling — the model deciding *when* and *how* to invoke functions — is a capability that scales hard with model size. Smaller models often fail at it.

The lesson is the talk's "decision framework" again, applied to a new dimension: not "local vs cloud," but "which task fits which model." Lab 1's local model was great for casual Q&A. Lab 3's local model is going to struggle with structured tool use. Same model, different task.

Pick the right model for the job. That's the workshop, condensed to one sentence.

## Where this fits in the workshop arc

Lab 3 is the bridge from "LLM that answers questions" (Labs 1-2) to "LLM that does things" (Lab 4 and beyond). The agent in Lab 3 is the brain. Lab 4 is the face.

After Lab 3 you'll understand why **MCP** (Model Context Protocol, the emerging standard you've probably heard about) exists. MCP is what happens when you take this tool-calling pattern and standardize it across applications — so an agent in Cursor can use tools defined for Claude Desktop without a custom integration each time. We may touch on it in the bonus discussion at the end of the workshop.
