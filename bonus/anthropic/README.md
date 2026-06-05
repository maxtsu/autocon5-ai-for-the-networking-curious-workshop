# Bonus: Anthropic — Same Workshop, Different Provider

**Time:** ~5 min
**Prerequisites:** Lab 3 or Lab 4 completed.

The talk is called "Choose Your Own AI Adventure." This is the smallest possible demonstration of why — swap OpenAI for Anthropic Claude in code you've already written, and see what changes.

## Why bother?

Three reasons to know how to swap providers:

1. **Vendor risk.** Single-provider dependency is a real production concern. Outages happen; pricing changes; terms of service change. Knowing your code works against two providers is the cheapest insurance.
2. **Capability differences.** No two models are identical. Claude is often noticeably stronger on long-context reasoning and following complex instructions; GPT models often shine on raw speed and cost at the small end. Empirical comparison on *your* workload beats marketing benchmarks.
3. **The talk's framing.** "Choose Your Own AI Adventure" only works if you've actually walked through more than one adventure. This is the cheapest second adventure.

## Setup

```bash
pip install "langchain-anthropic<1.0"
```

The `<1.0` pin matters: `langchain-anthropic` 1.x requires `langchain-core` 1.x, which is incompatible with the `langchain-openai` and `langchain-ollama` versions baked into this image (both on the 0.3.x line). Without the pin, the other providers in Labs 1-4 stop working.

Get an Anthropic API key:

1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Add some credit (~$5 will more than cover this lab; the small Claude models are inexpensive)
3. Generate an API key
4. Add to your `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

## The swap

Open `Lab_3_LangChain_Network_Agent/agent.py` (or your Lab 4 `chat_app.py`). Find this block:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

Change it to:

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-haiku-4-5", temperature=0)
```

> **A note on model strings.** Anthropic's current naming uses the family-tier-version pattern (`claude-haiku-4-5`, `claude-sonnet-4-7`, etc.). If `claude-haiku-4-5` errors with "model not found," check the current models page at [docs.anthropic.com/en/docs/about-claude/models](https://docs.anthropic.com/en/docs/about-claude/models) and use whatever the current Haiku-tier model identifier is. Anthropic publishes both rolling aliases and pinned snapshot IDs.

Re-run. That's it. The agent works identically — same tools, same prompt, same questions, different brain.

## What to compare

Run the same four questions from Lab 3 with both providers. Notice:

- **Tone and style.** Claude tends to be more cautious and explanatory; GPT tends to be more direct. Neither is "better" — they're different.
- **Tool-calling reliability.** Both Haiku-tier models handle tool-calling well. Bigger Claude models (Sonnet, Opus) handle complex multi-tool chains noticeably better than gpt-4o-mini does.
- **Latency.** First-token latency is roughly comparable. Total response time varies more by question than by provider.
- **Cost per call.** Both pricing tiers are similar at the small-model level. Pricing structures differ — Anthropic charges per million input/output tokens, OpenAI similarly. Check current rates.

## Going Further

### 1. Run all four labs against Claude

Lab 1 (raw API calls) needs the most adaptation — Anthropic's Messages API has a different shape from OpenAI's Chat Completions. The LangChain wrapper hides this; the raw SDK doesn't. Worth looking at both side-by-side to understand the abstraction LangChain provides.

### 2. Mix providers within one agent

There's no rule that says "all the LLM calls in your pipeline must come from one provider." A common pattern: use Claude for the high-stakes reasoning step and a cheaper model (gpt-4o-mini, Haiku, or a local Ollama model) for cheap auxiliary tasks like input classification or response formatting. The agent code doesn't care.

### 3. Try Anthropic's prompt caching

Anthropic supports prompt caching — repeating the same large system prompt across many calls becomes much cheaper because the prompt is cached server-side. For agents with long static context (large tool descriptions, big reference docs), this is a significant cost reduction. See the `cache_control` parameter in LangChain's `ChatAnthropic`.

### 4. Build a provider abstraction layer

For production, you probably want to encapsulate the choice of provider behind your own interface — `get_llm(name)` returning a unified object. This makes A/B testing painless and removes the provider mention from your business logic. LiteLLM, LangChain's own routing, and OpenRouter are three off-the-shelf options.
