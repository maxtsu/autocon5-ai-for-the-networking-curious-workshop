# Lab 2 Concepts: Prompt Engineering for Network Tasks

> 10-15 min introduction before hands-on starts.

## The big picture

In Lab 1 you made an LLM produce text. That's a start. But it's not enough to build software on.

Try this experiment in your head: send the same prompt to ChatGPT three times. You'll get three different responses — different tone, different format, different level of detail. Sometimes a bulleted list, sometimes prose, sometimes JSON. For casual chat that's fine. For software, it's a nightmare.

Lab 2 is about closing the gap from "the model said something reasonable" to "the model returned exactly what my code expects, every time."

## From "vibe prompting" to disciplined engineering

The talk calls this transition: vibe coding → disciplined engineering. Here's what it looks like at the prompt level.

**Vibe prompting:**

> *"Hey AI, here's some BGP output, give me the neighbors."*

Output varies every run. Sometimes JSON-ish, sometimes a paragraph, sometimes bullet points. Code that parses this is brittle. Change the prompt slightly, the parser breaks. Six months later, you can't reason about why production is flaky.

**Disciplined engineering:**

> *"Parse this BGP output. Return a list of objects with these exact fields: peer_ip (string), peer_as (integer), state (string). If a peer is in 'active' state, include a one-sentence diagnosis citing this reference data: [reference text...]"*

Output is consistent, validated, and your code never has to defensively parse model output again.

Lab 2 walks you through this transformation in four steps. Each step adds one discipline and fixes one failure mode of the previous step.

## The four techniques

```
   ┌─────────────────┐
   │   Step 1:       │   "Hey AI, give me the neighbors."
   │   Naive prompt  │   → inconsistent format, unusable in code
   └────────┬────────┘
            │ Add an example to imitate
   ┌────────▼────────┐
   │   Step 2:       │   "Here's an example of the format I want..."
   │   Few-shot      │   → consistent format, but still strings
   └────────┬────────┘
            │ Add a Pydantic schema
   ┌────────▼────────┐
   │   Step 3:       │   "Return data matching this schema..."
   │   Structured    │   → validated Python objects out
   └────────┬────────┘
            │ Add reference data
   ┌────────▼────────┐
   │   Step 4:       │   "Use this reference to diagnose..."
   │ Context-injected│   → accurate AND structured (simple RAG)
   └─────────────────┘
```

Each technique solves a specific failure mode:

| Technique             | Fixes                       | Cost                             |
|-----------------------|-----------------------------|----------------------------------|
| **Few-shot**          | Inconsistent output format  | A few example sentences          |
| **Structured (Pydantic)** | Almost-JSON / parse errors  | A schema class definition       |
| **Context injection** | Hallucinated facts          | A paragraph of reference data    |

By the end of the lab, your "naive call to gpt-4o-mini" has become a `parse_bgp_neighbors(raw_output) -> BgpNeighborList` function — typed, validated, ready to drop into Lab 3 as a tool an agent can call.

## A word about RAG

Step 4's context injection is **Retrieval-Augmented Generation** in its simplest form.

"Real" RAG embeds your reference documents into a vector database, retrieves the most relevant ones at query time, and stuffs them into the prompt automatically. We're skipping the retrieval mechanics — for this lab the reference data is hardcoded — but the prompting half is identical, and that's the half that matters most.

If you want to add real retrieval later, it's an upgrade to Step 4, not a rewrite. The system is built to be RAG-able.

## Why this matters

Every modern LLM-based application is built on these four primitives. ChatGPT's "advanced data analysis" mode is few-shot + structured output + tool calls. Cursor's code generation is structured output + context injection from your codebase. The pattern shows up everywhere because the failure modes are universal — naive prompts produce unreliable output, and every production team eventually rediscovers these techniques the hard way.

Twenty-five minutes from now you'll have built (small versions of) the same primitives the big AI companies are building on.

## Where this fits in the workshop arc

The Lab 2 analyzer becomes the first **tool** in Lab 3's agent. Whatever schema discipline you build here, the agent inherits. The cleaner your parsing function is, the more useful your agent gets.

Worth the discipline.
