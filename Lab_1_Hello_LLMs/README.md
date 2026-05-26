# Lab 1: Hello LLMs — Local and Cloud

**Time:** ~25 minutes

Make your first calls to a local LLM (Ollama running `llama3.2:3b`) and a cloud LLM (OpenAI's `gpt-4o-mini`). By the end of this lab you'll have:

- A working sense of how local vs. cloud LLMs differ in speed, quality, and cost
- Three small Python scripts that call each provider, including one that switches providers with a single line of code
- Hands-on time in Open WebUI — a chat GUI that talks to your local Ollama

This lab doesn't touch the network topology — it's purely about getting comfortable calling LLMs.

## Prerequisites

- You launched the Codespace and saw the welcome banner from `postCreate.sh`.
- `ollama --version` returns `0.23.1`.
- Your `.env` file has a real `OPENAI_API_KEY` (we'll verify this in Step 4).

## Concepts

- **Local vs cloud LLMs.** Local (Ollama) means the model runs on your Codespace's CPU — private, free, slower, smaller. Cloud (OpenAI) means a request leaves your machine — faster, sharper answers, pay-per-token.
- **The same API shape.** Both Ollama and OpenAI expose chat-completion APIs with the same `messages` array structure. This is not a coincidence; Ollama deliberately mirrors OpenAI.
- **LangChain as a thin abstraction.** Write your application code once against LangChain's interface, and swap providers with one constructor change. We'll exploit this heavily in Labs 2-4.

---

## Step 1: Start the Ollama daemon

Ollama doesn't auto-start in this Codespace — we start it deliberately so you see the "infrastructure must run before you can use it" pattern. (This same pattern shows up for containerlab in Lab 3.)

In a Codespace terminal:

```bash
ollama serve > /tmp/ollama.log 2>&1 &
sleep 3
```

Verify it's responding:

```bash
curl -s http://localhost:11434/ && echo "  ← Ollama is responding"
```

**Expected output:**
```
Ollama is running  ← Ollama is responding
```

Confirm the baked-in model is available:

```bash
ollama list
```

**Expected:** `llama3.2:3b` with size `2.0 GB`.

> **Troubleshooting:** If `curl` fails with `Failed to connect`, the daemon didn't start. Check `cat /tmp/ollama.log` for errors. The most common cause is port 11434 already in use — `pkill ollama` and retry.

---

## Step 2: First call via the CLI

The fastest way to talk to a local LLM is the `ollama` CLI. Try this:

```bash
ollama run llama3.2:3b "Explain BGP in one sentence."
```

**Expected:** A 1-2 sentence response about BGP, streamed token-by-token. The first call may take 5-10 seconds to "warm up" while the model loads into memory; subsequent calls return in 1-2 seconds.

Try a couple more prompts to get a feel for what a 3B-parameter model can and can't do:

```bash
ollama run llama3.2:3b "What is the default OSPF hello interval?"
ollama run llama3.2:3b "Write an SR Linux command to show BGP neighbors."
```

Notice that responses on well-known topics are reasonable, but the model may fabricate specifics on niche topics (this is hallucination — a core theme of Lab 2).

---

## Step 3: First call via Python (raw Ollama SDK)

CLI is fine for spot checks. For automation, we use Python.

Create `hello_ollama.py` in this lab folder with the following content:

```python
"""hello_ollama.py — first call to the local LLM via Python."""
from ollama import Client

client = Client(host="http://localhost:11434")

response = client.chat(
    model="llama3.2:3b",
    messages=[
        {"role": "user", "content": "Explain OSPF in one sentence."}
    ],
)

print(response["message"]["content"])
```

Run it:

```bash
python Lab_1_Hello_LLMs/hello_ollama.py
```

**Expected output:** A 1-2 sentence explanation of OSPF.

Notice the API structure: `client.chat()` takes a list of `messages` (each a dict with `role` and `content`), and returns a dict where the answer lives at `response["message"]["content"]`. That's the same shape OpenAI uses — a deliberate design choice on Ollama's part.

---

## Step 4: First call to OpenAI

Time to make a cloud LLM call. First, verify your key is loading.

Open `.env` in the file explorer (root of the workspace) and confirm `OPENAI_API_KEY=sk-...` has a real value, not blank. If it's still blank, grab a key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys) and make sure your account has at least $5 in prepaid credit.

Create `hello_openai.py` in this lab folder:

```python
"""hello_openai.py — first call to OpenAI's gpt-4o-mini via Python."""
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # reads .env, sets OPENAI_API_KEY in environment
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Explain OSPF in one sentence."}
    ],
)

print(response.choices[0].message.content)
print(f"\nTokens: prompt={response.usage.prompt_tokens}, completion={response.usage.completion_tokens}")
```

Run it:

```bash
python Lab_1_Hello_LLMs/hello_openai.py
```

**Expected:** A 1-2 sentence OSPF explanation, followed by a `Tokens: ...` line showing roughly 13 prompt tokens and 30-50 completion tokens. Cost is a fraction of a cent.

Compare against Step 3:
- **Speed:** OpenAI typically comes back in 0.5-1.5s — faster than Ollama (2-5s).
- **Quality:** gpt-4o-mini is a stronger model than llama3.2:3b. You'll usually notice the answers are tighter and more precise.
- **Cost:** You pay per token. Track it from the start.

> **Troubleshooting:** If you see `AuthenticationError`, your key isn't loading. Diagnose with:
> ```bash
> python -c "import os; from dotenv import load_dotenv; load_dotenv(); k = os.getenv('OPENAI_API_KEY'); print(k[:10] + '...' if k else 'KEY NOT SET')"
> ```
> Should print the first 10 chars of your key. If it says `KEY NOT SET`, `.env` isn't being read — make sure you're running Python from the workspace root (or the lab folder, since `load_dotenv()` walks up looking for `.env`).
>
> If you see `RateLimitError` saying "insufficient quota," your key is valid but the OpenAI account has no credit. Add $5 at [platform.openai.com/settings/organization/billing](https://platform.openai.com/settings/organization/billing).

---

## Step 5: Same code, both providers — via LangChain

Here's the punchline of this lab: with LangChain, the exact same Python code can drive either provider. You swap them by changing the constructor.

Create `compare.py` in this lab folder:

```python
"""
compare.py — Send the same prompt to both Ollama and OpenAI,
print responses side-by-side. Demonstrates LangChain's provider abstraction.
"""
import time
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()

PROMPT = "In one sentence, explain why BGP uses TCP instead of UDP."


def ask(llm):
    """Send the prompt, time the call, return (response_text, elapsed_seconds)."""
    start = time.time()
    response = llm.invoke([HumanMessage(content=PROMPT)])
    elapsed = time.time() - start
    return response.content, elapsed


# Same interface, different providers
ollama = ChatOllama(model="llama3.2:3b", base_url="http://localhost:11434")
openai = ChatOpenAI(model="gpt-4o-mini", temperature=0)

print(f"Prompt: {PROMPT}\n")

for llm, label in [(ollama, "Ollama / llama3.2:3b"),
                   (openai, "OpenAI / gpt-4o-mini")]:
    text, elapsed = ask(llm)
    print(f"=== {label} ({elapsed:.2f}s) ===")
    print(text)
    print()
```

Run it:

```bash
python Lab_1_Hello_LLMs/compare.py
```

**Expected output:** Two responses to the same prompt, with elapsed time stamped on each section. Typical timing:
- OpenAI: 0.5-1.5s
- Ollama: 2-5s

Notice what's identical and what's different:

- **Identical:** the call site is `llm.invoke([HumanMessage(...)])`. The same function call works for both providers.
- **Different:** the constructor — `ChatOllama(...)` vs `ChatOpenAI(...)`.

This is the abstraction we'll lean on in Labs 2-4. Application code doesn't need to know whether it's talking to a local or cloud model, which makes the "swap providers based on data sensitivity" pattern from the AC5 talk a one-line change in practice.

---

## Step 6: The chat GUI — Open WebUI

For exploration (as opposed to scripting), a chat GUI is often nicer than the CLI. Open WebUI is already running in this Codespace.

In VS Code's **Ports** panel (bottom of the screen, click "Ports" tab if you don't see it):

1. Find port **8080** labeled **"Open WebUI"**.
2. It probably already auto-opened in a preview pane. If not, click the globe icon next to port 8080 to open in browser.

In Open WebUI:
1. There's no sign-up flow — `WEBUI_AUTH=False` was set in the workshop config.
2. Pick `llama3.2:3b` from the model dropdown (top-left of the chat area). If the dropdown is empty, you didn't start Ollama in Step 1 — go back and do that, then refresh this page.
3. Type a prompt in the chat box at the bottom and hit enter.

The responses stream the same way as Steps 2-3, but with conversation history you can scroll through. This is just a UI on top of the same Ollama daemon you've been using; if you stopped Ollama with `pkill ollama`, the UI would also stop working.

---

## Going Further

If you finish the core lab early — or want to dig deeper later — try one or more of these:

### 1. A bigger Ollama model

`llama3.2:3b` is small and fast. `llama3.1:8b` is roughly 2-3x bigger and noticeably stronger — Meta's previous-generation 8B sits in the sweet spot of "fits in a 16GB Codespace, meaningfully better on network reasoning."

```bash
ollama pull llama3.1:8b   # ~4.7 GB download, 1-2 min on Codespace network
```

Edit `hello_ollama.py` and `compare.py` to use `llama3.1:8b` instead of `llama3.2:3b`. Re-run. Notice both the quality improvement and the latency hit (probably 2-3x slower).

### 2. gpt-4o vs gpt-4o-mini

Change `model="gpt-4o-mini"` to `model="gpt-4o"` in `hello_openai.py`. Re-run. Compare:
- Response quality (gpt-4o is meaningfully stronger on complex prompts)
- Token costs (`response.usage.completion_tokens` × the per-token price — gpt-4o is ~10x the cost per token of gpt-4o-mini)

The decision between them is rarely "which is better" and usually "which is good enough for this use case."

### 3. Streaming responses

Both providers support streaming. Instead of getting the whole response at once with `llm.invoke(...)`, you get chunks as the model generates them — useful for chatty UIs where the user sees text appear word-by-word instead of waiting in silence.

In `compare.py`, the `ask()` function currently looks like this (lines 16-21):

```python
def ask(llm):
    """Send the prompt, time the call, return (response_text, elapsed_seconds)."""
    start = time.time()
    response = llm.invoke([HumanMessage(content=PROMPT)])
    elapsed = time.time() - start
    return response.content, elapsed
```

Replace it with this streaming version:

```python
def ask(llm):
    """Stream the response chunk-by-chunk, return (full_text, elapsed_seconds)."""
    start = time.time()
    chunks = []
    for chunk in llm.stream([HumanMessage(content=PROMPT)]):
        print(chunk.content, end="", flush=True)   # print each chunk as it arrives
        chunks.append(chunk.content)
    print()                                         # newline once the stream ends
    elapsed = time.time() - start
    return "".join(chunks), elapsed
```

Re-run `python Lab_1_Hello_LLMs/compare.py`. You'll see Ollama's response appear word-by-word in real time, then OpenAI's. The `text` value returned by `ask()` is still the full response, so the existing `print(text)` line below the loop will redundantly re-print each answer after streaming — that's fine for the demo (and confirms the chunks were captured), or you can delete that line for a cleaner output.

**Why this matters:** streaming doesn't make the model faster — total elapsed time is the same. What it changes is *perceived* latency: the user sees motion immediately instead of staring at a frozen prompt for 3 seconds. Every chat UI you've ever used (ChatGPT, Claude, Open WebUI in Step 5) does this.

### 4. Median latency, not single-shot

Right now `compare.py` calls `ask()` once per provider. A single slow call — model cold-start, garbage-collection pause, a network blip — skews the elapsed-time number. Median across multiple runs is more honest.

Modify the comparison loop at the bottom of `compare.py` (lines 28-35). Replace it with this version that runs each prompt N times and reports the median:

```python
import statistics

N = 5

print(f"Prompt: {PROMPT}\n")

for llm, label in [(ollama, "Ollama / llama3.2:3b"),
                   (openai, "OpenAI / gpt-4o-mini")]:
    times = []
    for i in range(N):
        text, elapsed = ask(llm)
        times.append(elapsed)
        print(f"  run {i+1}: {elapsed:.2f}s")
    median = statistics.median(times)
    print(f"=== {label} — median of {N} runs: {median:.2f}s ===")
    print(text)   # last response — eyeball quality
    print()
```

Add `import statistics` at the top with the other imports (it's in Python's standard library — nothing to install).

Re-run `python Lab_1_Hello_LLMs/compare.py`. Typical pattern:

- **Ollama:** first call is meaningfully slower than calls 2-5 — that's the 3B model warming up in CPU memory. The median ignores that outlier.
- **OpenAI:** no local warm-up, so all 5 calls cluster more tightly, but you'll still see network-jitter variance of a few hundred ms.

**Cost note:** this sends the prompt 10 times total (5 runs × 2 providers). For OpenAI gpt-4o-mini that's a fraction of a cent — but worth understanding that "measure latency properly" comes with a real (small) bill on cloud providers.

### 5. Add Anthropic as a third provider

`langchain-anthropic` is already in the pre-built image — no `pip install` needed. Three steps to add Claude alongside Ollama and OpenAI.

**Step 1: Get an Anthropic API key.** Go to [console.anthropic.com](https://console.anthropic.com), sign up (or sign in), grab the $5 in starter credits, and create an API key. It'll look like `sk-ant-...`.

**Step 2: Add the key to `.env`.** Open `.env` in this Codespace (the file `postCreate.sh` copied from `.env.example` on Codespace startup) and add a line:

```
ANTHROPIC_API_KEY=sk-ant-...
```

The `load_dotenv()` call at the top of `compare.py` auto-reads this into environment variables, and `ChatAnthropic` picks it up from there — no need to pass the key explicitly in code.

**Step 3: Add three lines to `compare.py`.**

a) Add the import near the other LangChain imports (after line 8):

```python
from langchain_anthropic import ChatAnthropic
```

b) Add the constructor next to `ollama` and `openai` (after line 26):

```python
anthropic = ChatAnthropic(model="claude-haiku-4-5", temperature=0)
```

c) Add a third entry to the comparison loop (line 30-31):

```python
for llm, label in [(ollama, "Ollama / llama3.2:3b"),
                   (openai, "OpenAI / gpt-4o-mini"),
                   (anthropic, "Anthropic / claude-haiku-4-5")]:
```

Re-run `python Lab_1_Hello_LLMs/compare.py`. You'll get a three-way side-by-side: local Llama, cloud OpenAI, cloud Anthropic. Notice that the answers vary in *style* even with the same prompt and same `messages` shape — different model lineages produce noticeably different prose. The `bonus/anthropic/` folder goes deeper on what's specifically different about Anthropic's API and where Claude tends to shine for network workflows.

---

## What's next

In **Lab 2 (Prompt Engineering)** we'll stop accepting whatever the LLM gives back and start *constraining* it — few-shot examples, JSON-schema output, and the specific patterns that matter for network configuration tasks. We'll use the LangChain interface from Step 5 throughout, so the provider switch becomes free.
