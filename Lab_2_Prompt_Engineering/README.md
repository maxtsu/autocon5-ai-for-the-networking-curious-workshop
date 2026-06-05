# Lab 2: Prompt Engineering for Network Tasks

**Time:** ~25 minutes

Build a small Python tool that takes raw SR Linux BGP output and returns structured, validated, network-engineer-friendly facts. Along the way you'll experience four prompting techniques, each one fixing a specific failure mode of the previous: naive prompts (baseline), few-shot examples (consistency), JSON schemas via Pydantic (parseable output), and context injection (a simple form of RAG for accuracy).

By the end, this raw output:

```
| default       | 10.1.13.2            | ebgp-r3       | S    | 65002  | active     |
```

Will reliably become this Python object:

```python
BgpNeighbor(
    peer_ip='10.1.13.2',
    group='ebgp-r3',
    peer_as=65002,
    state='active',
    diagnosis="Active state means the local router cannot complete TCP/179 to 10.1.13.2 — usually a peer config issue on the remote side, not local reachability."
)
```

The parser you build here reappears in Lab 3, wrapped in an agent that calls it autonomously.

## Prerequisites

- Lab 1 completed (Ollama daemon running, OpenAI key working).
- Comfortable with Python's class syntax — we'll use Pydantic to define schemas.

## Concepts

- **Naive prompts produce inconsistent output.** Same input, different format every run. Hard to build on.
- **Few-shot prompting** gives the model concrete examples to imitate. Consistency improves.
- **Structured output via Pydantic** turns "the model returned text that looks like JSON" into "the model returned a validated Python object." Schema becomes a contract.
- **Context injection** is the simplest form of Retrieval-Augmented Generation: stuff the relevant reference material into the prompt. Real RAG retrieves dynamically; this one is a hardcoded shortcut, but the principle is identical.

---

## Step 1: The naive baseline — and why it fails

Create `naive_parser.py` in this lab folder:

```python
"""naive_parser.py — what happens when you just ask the LLM to do it."""
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

SAMPLE = """
+---------------+----------------------+---------------+------+--------+------------+
|   Net-Inst    |         Peer         |     Group     | Flags| Peer-  |   State    |
|               |                      |               |      |   AS   |            |
+===============+======================+===============+======+========+============+
| default       | 10.0.0.2             | ibgp-65001    | S    | 65001  | established|
| default       | 10.1.13.2            | ebgp-r3       | S    | 65002  | active     |
+---------------+----------------------+---------------+------+--------+------------+
"""

prompt = f"Extract the BGP neighbors from this output:\n{SAMPLE}"
response = llm.invoke(prompt)
print(response.content)
```

Run it **three times** in a row:

```bash
python Lab_2_Prompt_Engineering/naive_parser.py
python Lab_2_Prompt_Engineering/naive_parser.py
python Lab_2_Prompt_Engineering/naive_parser.py
```

**Expected:** Each run can give a different format. One might return a bulleted list, another a Markdown table, another a paragraph of prose, another a code-fenced JSON-ish blob that isn't quite valid JSON. Even with `temperature=0`, the model has too much freedom in *how* to present the answer. (Depending on the model, the three runs may sometimes look similar — newer models are more consistent. The point isn't that the format *always* changes; it's that nothing *guarantees* it stays the same, so you can't safely build a parser on it.)

**This is the problem.** You can't build software on output you can't predict. Every subsequent step in this lab is a different fix for this exact failure mode.

> **Why doesn't `temperature=0` make it consistent?** `temperature=0` makes token sampling deterministic given the same prompt and context, but the prompt itself doesn't constrain the *format* of the answer. The model is free to "decide" on a bulleted list one time and JSON the next, because nothing told it which to use.

---

## Step 2: Few-shot prompting — give it an example

> **Heads up — this file is already in the repo.** `few_shot_parser.py` is here in this lab folder as a reference starting point. Open it and follow along, or, if you want the challenge, delete it and write it yourself from the steps. Either way works.

Here's `few_shot_parser.py`:

```python
"""few_shot_parser.py — same task, but with an example output to imitate."""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

SYSTEM_PROMPT = """You are a network configuration parser. Given SR Linux BGP neighbor
output, extract each peer and return one JSON object per line, no commentary.

Example input:
| default       | 192.168.1.1          | example-grp   | S    | 65500  | established|

Example output:
{"peer_ip": "192.168.1.1", "group": "example-grp", "peer_as": 65500, "state": "established"}
"""

SAMPLE = """
| default       | 10.0.0.2             | ibgp-65001    | S    | 65001  | established|
| default       | 10.1.13.2            | ebgp-r3       | S    | 65002  | active     |
"""

response = llm.invoke([
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content=SAMPLE),
])
print(response.content)
```

Run it three times.

**Expected:** Two JSON objects, one per line, in the format the example specified. Consistent across runs. No commentary, no bullets, no prose.

**The fix:** The example acts as an implicit contract. The model treats "give me output like this example" much more reliably than "give me output that I'll be happy with." Few-shot is the cheapest, most-bang-for-buck prompting technique.

> **Why does a single example help so much?** LLMs are pattern-completion engines. Showing one input/output pair turns the task from "interpret a vague instruction" into "complete the pattern" — which models are exceptionally good at. Two or three examples help a bit more; the marginal gain drops off fast.

---

## Step 3: Structured output via Pydantic — no more JSON.loads()

Few-shot fixes format but doesn't *guarantee* parseable JSON. The model could still emit "almost-JSON" that breaks `json.loads()` on edge cases (a missing quote, a trailing comma). LangChain solves this with `with_structured_output()` — you give it a Pydantic schema, and the LLM is forced to return data that matches the schema, validated.

> **Heads up — this file is already in the repo.** `structured_parser.py` is here in this lab folder as a reference starting point. Open it and follow along, or, if you want the challenge, delete it and write it yourself from the steps. Either way works.

Here's `structured_parser.py`:

```python
"""structured_parser.py — Pydantic schemas as a contract with the LLM."""
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


class BgpNeighbor(BaseModel):
    """A single BGP peering session."""
    peer_ip: str = Field(description="IP address of the BGP peer")
    group: str = Field(description="Peer group name this neighbor belongs to")
    peer_as: int = Field(description="Peer's autonomous system number")
    state: str = Field(description="BGP session state (established, active, idle, etc.)")


class BgpNeighborList(BaseModel):
    """Top-level container for a list of neighbors."""
    neighbors: list[BgpNeighbor]


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(BgpNeighborList)

SAMPLE = """
| default       | 10.0.0.2             | ibgp-65001    | S    | 65001  | established|
| default       | 10.1.13.2            | ebgp-r3       | S    | 65002  | active     |
"""

result = llm.invoke(f"Extract the BGP neighbors:\n{SAMPLE}")

# result is a BgpNeighborList — a real Python object, not a string
for n in result.neighbors:
    print(f"  {n.peer_ip}  AS{n.peer_as:<6}  {n.state}")
```

Run it:

```bash
python Lab_2_Prompt_Engineering/structured_parser.py
```

**Expected:**
```
  10.0.0.2  AS65001  established
  10.1.13.2 AS65002  active
```

Notice what's happening here:

- The LLM call returns a `BgpNeighborList` object, not a string. No `json.loads()` is needed.
- The `peer_as` field is typed as `int` — if the LLM returns "65001" as a string, Pydantic coerces it. If it returns garbage that can't be coerced, the call raises a validation error rather than silently corrupting your downstream code.
- The `Field(description=...)` text is passed to the LLM as part of the schema, helping it understand what each field means.

**The contract is the value.** Once you have a Pydantic-validated object, you can build software on it the same way you'd build on any other typed object. Your code never has to defensively parse model output again.

---

## Step 4: Context injection — fight hallucination with reference data

Schemas give you a clean *shape*. They don't help with *correctness*. If you ask the LLM to diagnose a BGP state and the model misremembers what "active" means, you'll get a confidently wrong diagnosis in a beautifully structured object — the worst kind of failure.

The cheapest fix: paste relevant reference material into the prompt. This is the simplest form of Retrieval-Augmented Generation. Real RAG does retrieval dynamically from a vector store; we'll just hardcode the reference text and see the principle.

> **Heads up — this file is already in the repo.** `analyzer.py` is here in this lab folder as a reference starting point. Open it and follow along, or, if you want the challenge, delete it and write it yourself from the steps. Either way works.

Here's `analyzer.py` — this is the "real" tool we'll keep using:

```python
"""analyzer.py — combines few-shot + structured output + context injection."""
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

# The "retrieved" knowledge. In real RAG this would come from a vector
# store keyed off the user's question; here we inline it because the
# scope is fixed (BGP state interpretation).
BGP_REFERENCE = """
BGP session states, per RFC 4271:
- idle:        starting state, no resources allocated
- connect:     trying to complete TCP/179 connection to peer
- active:      TCP connection failed, retrying. Usually indicates the
               peer is not configured to accept this session — check
               peer-side config, not local reachability.
- opensent:    TCP up, OPEN message sent, waiting for peer's OPEN
- openconfirm: peer's OPEN accepted, waiting for KEEPALIVE
- established: session up, prefixes are being exchanged
"""


class BgpNeighbor(BaseModel):
    peer_ip: str = Field(description="IP address of the BGP peer")
    group: str = Field(description="Peer group name")
    peer_as: int = Field(description="Peer AS number")
    state: str = Field(description="BGP session state")
    diagnosis: str = Field(
        description="One-sentence explanation of what this state means "
                    "operationally, citing the reference data."
    )


class BgpNeighborList(BaseModel):
    neighbors: list[BgpNeighbor]


SYSTEM_PROMPT = f"""You are a network engineer parsing SR Linux BGP output.

Use this reference to diagnose each session:
{BGP_REFERENCE}

If you don't have enough information to diagnose, say "insufficient data" — do not guess.
"""

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(BgpNeighborList)

SAMPLE = """
| default       | 10.0.0.2             | ibgp-65001    | S    | 65001  | established|
| default       | 10.1.13.2            | ebgp-r3       | S    | 65002  | active     |
"""

result = llm.invoke([
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content=f"Parse and diagnose:\n{SAMPLE}"),
])

for n in result.neighbors:
    print(f"{n.peer_ip} ({n.state}, AS{n.peer_as})")
    print(f"  → {n.diagnosis}\n")
```

Run it:

```bash
python Lab_2_Prompt_Engineering/analyzer.py
```

**Expected output:** Two neighbors with diagnosis fields. The diagnosis for `10.1.13.2` (state: active) should mention something close to "TCP connection failing, check peer-side config" — exactly the conclusion you'd reach by reading the reference data.

Without `BGP_REFERENCE` in the prompt, the model often produces a plausible-sounding but inaccurate diagnosis (e.g., "active means the session is active and working" — which is wrong; that means `established`). The reference data anchors the model to the actual definitions.

**Try the experiment:** comment out the `Use this reference to diagnose each session:\n{BGP_REFERENCE}` line, re-run, and compare. You'll often see the model invent definitions. This is the hallucination guardrail that matters most in practice.

---

## Step 5: Try it with Ollama

Same code, different provider. Modify the `llm` line in `analyzer.py`:

```python
# Replace this:
# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(BgpNeighborList)

# With this:
from langchain_ollama import ChatOllama
llm = ChatOllama(model="llama3.2:3b", base_url="http://localhost:11434").with_structured_output(BgpNeighborList)
```

Run it.

**Expected:** Output that's structurally similar but noticeably weaker. The 3B-parameter local model may:
- Skip the diagnosis field or fill it with vague text
- Mis-parse one of the rows (conflate two columns, e.g. merge the Peer-AS and State fields, or mislabel the peer group)
- Get the schema right but the content wrong

> **Heads up — this may not succeed on the first try, and that's part of the point.** Local-model output is non-deterministic: run the same prompt twice and you can get different results. With a small model you may hit a Pydantic `ValidationError` — something like:
>
> ```
> pydantic_core._pydantic_core.ValidationError: 1 validation error for BgpNeighborList
> ```
>
> — or get an empty neighbor list back. This is common on `llama3.2:3b`, and even more likely if you try a larger-but-still-modest model such as `llama3.1:8b` (it sometimes returns *no* neighbors, which fails validation). **That error is not a bug in the lab.** It's `with_structured_output()` *refusing* to hand you malformed data instead of letting it slip through silently — exactly the guardrail Step 3 was about. If you hit it, re-run a couple of times; if it persists, switch this step back to OpenAI. Production code would wrap the call in a retry / `try-except`; we keep the happy path here to stay focused on the prompting concepts.

**The lesson:** prompting techniques aren't magic. They help any model, but they help bigger models more. Local models trade off capability for privacy and zero marginal cost. Choosing between them isn't "which is best," it's "which is good enough for *this* task while meeting *these* data-sovereignty constraints" — exactly the talk's main point.

---

## Going Further

If you finish the core lab early:

### 1. "Say I don't know" — explicit anti-hallucination

The `BGP_REFERENCE` text in Step 4 included a sentence ending in `do not guess`. Remove it, re-run, and compare. Without the explicit instruction, models often guess when they shouldn't. Add the instruction back, and try a deliberately under-specified input ("Parse this empty string"). The model should now respond with `insufficient data` instead of fabricating.

### 2. Temperature tuning

We set `temperature=0` throughout this lab — deterministic for the same prompt, ideal for parsing. Try `temperature=0.7` on `analyzer.py` and re-run a few times. Notice the diagnosis text varies. Useful for creative tasks (Lab 4 will use higher temperature for chat); deadly for parsing.

### 3. Real RAG, not inline context

The `BGP_REFERENCE` was hardcoded. Real RAG retrieves from a vector store at query time. The shape:
- Embed your reference docs into a vector DB (FAISS, Chroma)
- At query time, embed the user's question, find the top-k most similar docs
- Inject those docs into the prompt

LangChain has `RetrievalQA` chains for this. It's a half-day on its own; skip for the workshop. The point here is that the *prompting* part is the same — you just construct the context dynamically.

### 4. Cross-vendor parsing

Generate a Cisco IOS `show ip bgp summary` output (ask the LLM to make one up if you don't have a real device). Run `analyzer.py` against it. Notice the parsing falls apart — the schema was implicitly trained on SR Linux's column shape. Add Cisco-format examples to a new system prompt to make the parser multi-vendor. This is one of the most realistic real-world use cases — different routers, same downstream code expecting the same structured object.

### 5. The parser becomes an agent tool

Wrap `analyzer.py`'s logic in a function with a clear signature:

```python
def parse_bgp_neighbors(raw_output: str) -> BgpNeighborList:
    """Parse SR Linux 'show bgp neighbor' output into structured data."""
    ...
```

This is exactly the shape Lab 3 will use to register this as a tool an agent can call. You've effectively written the first tool in your agent's toolkit.

---

## What's next

In **Lab 3 (LangChain Network Agent)**, you'll wrap this parser (and a couple more like it) as *tools* and hand them to a LangChain agent. The agent decides which tool to call based on the user's question — turning your parsing logic into something that feels like a real "network co-pilot."
