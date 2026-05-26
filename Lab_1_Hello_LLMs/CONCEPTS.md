# Lab 1 Concepts: Hello LLMs

> 10-15 min introduction before hands-on starts.

## The big picture

You've all used ChatGPT in a browser. What you're about to do is the same conversation — but happening inside your code. Programmatically, repeatably, automatable. That shift is the entire workshop, and it starts here.

Today's first hour gets the basics right:

- How does my code actually talk to an LLM?
- What's the difference between running one locally vs. calling one in the cloud?
- When should I choose one over the other?

By Lab 1's end you'll have made calls to both Ollama (local, on your Codespace) and OpenAI (cloud). And, the punchline, you'll have written exactly one Python script that talks to either — switching between them with a single line of code.

## Two kinds of LLMs: local vs cloud

|                          | **Local (Ollama)**         | **Cloud (OpenAI)**          |
|--------------------------|----------------------------|-----------------------------|
| Where the model runs     | Your machine               | Their data centers          |
| Cost per call            | Free (electricity only)    | Per-token, pennies-to-$$$   |
| Speed                    | Bound by your CPU/GPU      | Fast — they have GPUs       |
| Quality                  | Smaller models, weaker     | Frontier models, sharper    |
| Data leaves your network | No                         | Yes                         |
| Network required         | No (after first download)  | Yes, always                 |
| Privacy / sovereignty    | Total control              | Trust their data policies   |

This isn't "local good, cloud bad" or vice-versa. It's a series of trade-offs you make per task, per data sensitivity, per latency budget, per dollar budget.

The framework I want you to leave the workshop with:

> **Pick the smallest LLM that's good enough for the task, running as close to your data as the data's sensitivity demands.**

That single sentence shapes every decision in the rest of the workshop.

## The "same shape" promise

Here's what makes this practical: both Ollama and OpenAI expose chat-completion APIs that look the same.

Same `messages` array structure (`{role: "user", content: "..."}`). Same response shape (`choices[0].message.content`). Same basic invocation pattern. This isn't an accident — Ollama deliberately mirrors OpenAI's API surface.

What this means for your application code:

```
                  ┌──────────────────────────┐
   Your code ────►│       LangChain          │
                  │  (one interface for      │
                  │   any LLM provider)      │
                  └─────┬──────────┬─────────┘
                        │          │
                  ┌─────▼────┐ ┌───▼──────────┐
                  │  Ollama  │ │  OpenAI      │
                  │ (local)  │ │  (cloud)     │
                  └──────────┘ └──────────────┘
```

Two providers, one interface. You pick at runtime, based on the task.

## Why this matters at work

The talk's "Choose Your Own AI Adventure" framing comes from real choices teams make every day:

- **Logs that mention customer names** → can't go to a cloud LLM without legal review. Local model.
- **Marketing copy for next quarter's release** → no sensitive data, cloud LLM is fine, you want the best quality you can get.
- **A 3 AM on-call query about a routing issue** → speed matters more than perfect quality. Whichever responds first wins.

Once you've made a clean call to both in this lab, you've earned the right to have an opinion about which one to use, when. That opinion is the real takeaway.

## Where this fits in the workshop arc

Lab 1 is foundation. Every subsequent lab calls an LLM — Lab 2 calls it more carefully (prompting), Lab 3 wraps it in an agent, Lab 4 wraps the agent in a UI. If your LLM access is shaky, everything downstream wobbles.

Spend the 25 minutes here getting comfortable with the basics. The rest of the workshop is recipes built on this base.
