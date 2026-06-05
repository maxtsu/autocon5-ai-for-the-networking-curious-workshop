# Lab 3: Building a Network Agent with LangChain

**Time:** ~25 minutes

Build a LangChain agent that answers natural-language questions about your network by calling tools you define. The agent decides which tool to invoke, with which arguments, when to call it more than once, and when to skip tool-calling entirely and answer from its own knowledge.

By the end you'll be able to type:

```
What's BGP looking like on r1?
```

…and watch the agent autonomously fetch and parse the BGP state, then return a plain-English summary. This is the moment the workshop crosses from "LLM as smart text generator" into "LLM as something that can actually do work."

## Prerequisites

- Labs 1 & 2 completed
- Familiarity with Python decorators (we use `@tool`) and type hints

## Concepts

- **Agent vs. plain LLM call.** A plain LLM call is a single round-trip: prompt in, text out. An agent runs a *loop*: prompt → decide whether to use a tool → call it → observe the result → decide again → eventually answer. The agent reasons over its own intermediate results.
- **The tool abstraction.** A tool is a regular Python function decorated with `@tool`. LangChain reads its signature and docstring to teach the LLM what the tool does and when to use it. Tool descriptions matter a lot — they're effectively part of the prompt.
- **Why "agent with one tool" is still meaningful.** Even with a single tool, the agent decides *whether* to call it (skip for general questions like "what is BGP?"), *how* to call it (pick the right node), and *how to interpret* the result. That decision-making is the agentic part — not the number of tools.
- **Live vs. canned data.** Steps 1-4 use canned BGP outputs so the agent code works regardless of containerlab state. Step 5 then captures real BGP from the live topology and reruns the same agent against it — proving the abstraction holds across canned and live inputs.

---

## Step 1: Set up the sample data

The agent's tool reads BGP output from three text files. Create them in the lab's `sample_data/` folder:

```bash
mkdir -p Lab_3_LangChain_Network_Agent/sample_data
cd Lab_3_LangChain_Network_Agent/sample_data

cat > r1_bgp.txt <<'EOF'
+---------------+----------------------+---------------+------+--------+--------------+
|   Net-Inst    |         Peer         |     Group     | Flag | Peer-  |    State     |
|               |                      |               |  s   |   AS   |              |
+===============+======================+===============+======+========+==============+
| default       | 10.0.0.2             | ibgp-65001    | S    | 65001  | established  |
| default       | 10.1.13.2            | ebgp-r3       | S    | 65002  | established  |
+---------------+----------------------+---------------+------+--------+--------------+
EOF

cat > r2_bgp.txt <<'EOF'
+---------------+----------------------+---------------+------+--------+--------------+
|   Net-Inst    |         Peer         |     Group     | Flag | Peer-  |    State     |
|               |                      |               |  s   |   AS   |              |
+===============+======================+===============+======+========+==============+
| default       | 10.0.0.1             | ibgp-65001    | S    | 65001  | established  |
+---------------+----------------------+---------------+------+--------+--------------+
EOF

cat > r3_bgp.txt <<'EOF'
+---------------+----------------------+---------------+------+--------+--------------+
|   Net-Inst    |         Peer         |     Group     | Flag | Peer-  |    State     |
|               |                      |               |  s   |   AS   |              |
+===============+======================+===============+======+========+==============+
| default       | 10.1.13.1            | ebgp-r1       | S    | 65001  | established  |
+---------------+----------------------+---------------+------+--------+--------------+
EOF

cd ../..
ls Lab_3_LangChain_Network_Agent/sample_data/
```

**Expected:** Three files listed — `r1_bgp.txt`, `r2_bgp.txt`, `r3_bgp.txt`.

> These are condensed versions of real captured output from the containerlab topology. The full output has more columns (uptime, AFI/SAFI, [Rx/Active/Tx]); we trimmed them here to keep the focus on parsing logic. Step 5 captures the full real outputs and reruns the agent against them.

---

## Step 2: Define the tool

> **Heads up — this file is already in the repo.** `bgp_tool.py` is here in this lab folder as a reference starting point. Open it and follow along, or, if you want the challenge, delete it and write it yourself from the steps. Either way works.

Here's `bgp_tool.py`. This wraps Lab 2's analyzer in a function the agent can call.

```python
"""bgp_tool.py — single tool for fetching and parsing BGP state."""
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

SAMPLE_DATA = Path(__file__).parent / "sample_data"


# Schema reused from Lab 2
class BgpNeighbor(BaseModel):
    peer_ip: str = Field(description="IP address of the BGP peer")
    group: str = Field(description="Peer group name")
    peer_as: int = Field(description="Peer AS number")
    state: str = Field(description="BGP session state")
    diagnosis: str = Field(description="One-sentence operational diagnosis")


class BgpNeighborList(BaseModel):
    neighbors: list[BgpNeighbor]


BGP_REFERENCE = """
BGP session states per RFC 4271:
- idle:        starting state, no resources allocated
- connect:     trying to complete TCP/179 to peer
- active:      TCP connection failed; usually a peer-side config issue
- opensent:    TCP up, OPEN sent, waiting for peer's OPEN
- openconfirm: peer's OPEN accepted, waiting for KEEPALIVE
- established: session up, exchanging UPDATE messages
"""

analyzer = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(BgpNeighborList)


@tool
def get_bgp_state(node: str) -> str:
    """Get the BGP peering state for a node in the topology.

    Use this tool when the user asks about BGP neighbors, peering status,
    or session state on a specific router. Returns a structured summary
    of each BGP neighbor including peer IP, AS number, state, and diagnosis.

    Args:
        node: Node name. One of: 'r1', 'r2', 'r3'.

    Returns:
        Human-readable summary of all BGP neighbors on that node.
    """
    sample_file = SAMPLE_DATA / f"{node}_bgp.txt"
    if not sample_file.exists():
        return f"No BGP data for '{node}'. Available nodes: r1, r2, r3."

    raw_output = sample_file.read_text()
    result = analyzer.invoke([
        ("system", f"Parse and diagnose using:\n{BGP_REFERENCE}"),
        ("human", raw_output),
    ])

    lines = [f"BGP neighbors on {node}:"]
    for n in result.neighbors:
        lines.append(f"  - {n.peer_ip} (AS{n.peer_as}, group={n.group}, state={n.state})")
        lines.append(f"    Diagnosis: {n.diagnosis}")
    return "\n".join(lines)


# Quick standalone test
if __name__ == "__main__":
    print(get_bgp_state.invoke({"node": "r1"}))
```

Two parts of this file deserve a closer look:

- **The docstring is the prompt.** LangChain extracts the function's docstring and gives it to the LLM as part of the tool description. The phrase "Use this tool when the user asks about BGP neighbors, peering status, or session state on a specific router" is what teaches the agent *when* to reach for this tool vs. answering from its own knowledge. A vague docstring → a confused agent.
- **The return type is `str`, not `BgpNeighborList`.** Agents work best when tools return formatted text — easier for the LLM to read back and reason over. We do the Pydantic-validated parsing internally but flatten the result before returning. Internal validation, external simplicity.

Run it standalone to verify:

```bash
python Lab_3_LangChain_Network_Agent/bgp_tool.py
```

**Expected output:**
```
BGP neighbors on r1:
  - 10.0.0.2 (AS65001, group=ibgp-65001, state=established)
    Diagnosis: Session is up; prefixes are being exchanged.
  - 10.1.13.2 (AS65002, group=ebgp-r3, state=established)
    Diagnosis: Session is up; prefixes are being exchanged.
```

---

## Step 3: Build the agent

> **Heads up — this file is already in the repo, and it's already the finished version.** `agent.py` is here in this lab folder as a reference starting point — and note it already contains the *full Step 4* version (all four questions you'll see in the next step), not the single-question version shown here. So if you run it as-is right now, you'll see all four questions run, not just one. That's expected: read along with the single-question snippet below to see where we start, then Step 4 walks through the rest. For the challenge, delete the file and build it up yourself, one question at a time.

Here's the starting point for `agent.py`:

```python
"""agent.py — a tiny LangChain agent with one tool."""
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from bgp_tool import get_bgp_state

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a network engineering assistant. The user asks questions about a small "
     "containerlab topology with three nodes (r1, r2, r3). Use the available tools "
     "when the user asks about specific routers. For general questions ('what is BGP?') "
     "answer from your own knowledge — do not call tools when they aren't needed."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

tools = [get_bgp_state]

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    question = "What's BGP looking like on r1?"
    print(f"\nQuestion: {question}\n{'=' * 60}")
    result = executor.invoke({"input": question})
    print(f"\n{'=' * 60}\nFinal answer:\n{result['output']}")
```

Run it:

```bash
python Lab_3_LangChain_Network_Agent/agent.py
```

**Expected:** With `verbose=True`, you'll see something like:

```
> Entering new AgentExecutor chain...

Invoking: `get_bgp_state` with `{'node': 'r1'}`

BGP neighbors on r1:
  - 10.0.0.2 (AS65001, group=ibgp-65001, state=established)
    ...

r1 has two BGP neighbors, both in the established state...

> Finished chain.
```

The structure to notice:

1. The agent decided to call `get_bgp_state` with `node='r1'` — extracted from the natural-language question.
2. The tool ran and returned its summary text.
3. The agent saw that summary and used it to compose a plain-English final answer.

This is the **agent loop**: think → act → observe → think → answer.

---

## Step 4: Watch the reasoning across different questions

The interesting part of agents isn't watching one call — it's watching them *decide*. Modify the bottom of `agent.py` to run a list of questions:

```python
if __name__ == "__main__":
    questions = [
        "What is BGP?",                              # General — should not call any tool
        "What's BGP looking like on r1?",            # Specific — single tool call
        "Is r3 peering with r1?",                    # Specific — needs reasoning over result
        "Compare BGP state between r1 and r3.",      # Should call the tool twice
    ]

    for q in questions:
        print(f"\n{'=' * 70}\nQuestion: {q}\n{'=' * 70}")
        result = executor.invoke({"input": q})
        print(f"\nFinal answer:\n{result['output']}")
```

Re-run. Watch the verbose output carefully for each question:

- **Question 1** ("What is BGP?"): No tool call. The agent answers from its own training knowledge. Notice it didn't get tricked into calling the tool just because the word "BGP" appeared.
- **Question 2** ("What's BGP looking like on r1?"): One call to `get_bgp_state(node='r1')`. Standard tool use.
- **Question 3** ("Is r3 peering with r1?"): The agent has to reason — it can answer this by looking at r1's neighbor list or r3's, since either side shows the same peering. Notice which one it picks.
- **Question 4** ("Compare r1 and r3"): **Two tool calls** in sequence. The agent calls `get_bgp_state('r1')`, then `get_bgp_state('r3')`, then synthesizes both responses into a comparison.

This is the part that's worth dwelling on. The agent never received instructions like "for comparisons, call the tool twice." It worked that out on its own from the question structure.

---

## Step 5: Now with real data

We've proven the agent works against canned BGP outputs. Time to point it at the live topology — same parser, same agent, real input. This is where the lab crosses from "demo" into "actually inspecting a network."

### Deploy the topology

If your containerlab isn't already running:

```bash
cd /workspaces/autocon5-ai-workshop
containerlab deploy -t clab/topology.clab.yml
```

Wait ~30 seconds for the deploy to settle. You should see three nodes (`clab-autocon5-r1`, `r2`, `r3`) created and the summary table showing them all `running`.

### Check r3's eBGP neighbor — and fix it if it's missing

> **Why this step exists:** SR Linux 25.10's bulk startup-config push *sometimes* silently drops one BGP neighbor line on r3 when containerlab applies the startup configs. It's non-deterministic — on some deploys r3 comes up fully converged and there's nothing to do; on others the eBGP line to r1 never lands. The line is syntactically valid (the same syntax works on r1), it just doesn't always take in r3's context. So rather than fight containerlab's deploy pipeline, we **check r3 first and apply the missing line only if it's absent.** Either way you get a quick taste of SR Linux's commit-based CLI — and spotting and fixing these edge cases is part of real network automation.

SSH to r3:

```bash
ssh admin@clab-autocon5-r3    # password: NokiaSrl1!
```

First, check whether the eBGP neighbor to r1 (`10.1.13.1`) is already there:

```
show network-instance default protocols bgp neighbor
```

- **If you see neighbor `10.1.13.1` in the list** — r3 is fine, the line landed on this deploy. **Skip the fix**, type `quit`, and move on to the next section.
- **If `10.1.13.1` is missing** — apply it live:

```
enter candidate
set / network-instance default protocols bgp neighbor 10.1.13.1 peer-group ebgp-r1
commit now
quit
```

> **If you're not sure, it's safe to run the fix anyway** — re-applying the same `set` line when the neighbor already exists is a harmless no-op in SR Linux.

### Verify BGP is up across the topology

From the Codespace terminal:

```bash
ssh admin@clab-autocon5-r1    # password: NokiaSrl1!
```

Inside r1:

```
show network-instance default protocols bgp neighbor
```

**Expected:** two neighbors, both `established` — `10.0.0.2` (r2, iBGP) and `10.1.13.2` (r3, eBGP). If r3's session shows `active` or `connect`, wait 10 seconds and re-run; BGP's TCP/179 handshake plus OPEN/KEEPALIVE negotiation takes a beat to complete.

```
quit
```

### Capture real BGP output

Overwrite the canned files in `sample_data/` with live captures from each node. Run this loop and **type the password (`NokiaSrl1!`) when prompted — once per node:**

```bash
cd /workspaces/autocon5-ai-workshop

for NODE in r1 r2 r3; do
    ssh -o StrictHostKeyChecking=no admin@clab-autocon5-${NODE} \
        "show network-instance default protocols bgp neighbor" \
        > Lab_3_LangChain_Network_Agent/sample_data/${NODE}_bgp.txt
done

# Eyeball one to confirm the capture worked
head -25 Lab_3_LangChain_Network_Agent/sample_data/r1_bgp.txt
```

`ssh` prompts for the password on your terminal, so you'll be asked three times (once per node) — just type `NokiaSrl1!` each time.

> **Optional shortcut — `sshpass`.** If `sshpass` happens to be installed in your environment, you can skip the prompts by wrapping each call: `sshpass -p 'NokiaSrl1!' ssh -o StrictHostKeyChecking=no admin@clab-autocon5-${NODE} ...`. It isn't guaranteed to be present, so the password-prompt loop above is the path we rely on. (If you'd rather, you can also SSH into each node by hand, run the show command, and paste the output into the three `${NODE}_bgp.txt` files — same result.)

**Expected:** real BGP neighbor tables with the full column set — including `Uptime`, `AFI/SAFI`, and `[Rx/Active/Tx]` counters that weren't in the canned versions. Remember the note in Step 1 about trimming those columns? Now you've got them back.

### Re-run the agent against real data

```bash
cd Lab_3_LangChain_Network_Agent
python agent.py
```

**Expected:** the same four questions, the same agent code, the same parser — but now answering against the live BGP state of routers actually running in your Codespace. The "Compare BGP state between r1 and r3" answer should reflect the *real* counter values and uptimes the agent just observed.

### Why this matters

The parser doesn't care whether its input came from a file we shipped or a `show` command captured 30 seconds ago. The agent doesn't care that the tool is now talking to real routers instead of canned data. **That's the abstraction working.** When you take this pattern home, swapping `read_file()` for `ssh_and_capture()` is the entire production-ization step — every other line of code stays the same.

It's also why we cared about structured output in Lab 2. The real BGP table from r1 has columns the canned versions never had. The Pydantic schema only extracts the four fields it actually needs; everything else gets ignored gracefully. Schema-first parsing is what makes the same code work across canned and live inputs.

---

## Step 6: Provider swap — try with Ollama

Same lesson as Labs 1 & 2: swap the provider with one line and see what changes. Modify the `llm =` line in `agent.py`:

```python
# Comment out this:
# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Use this instead:
from langchain_ollama import ChatOllama
llm = ChatOllama(model="llama3.2:3b", base_url="http://localhost:11434", temperature=0)
```

Re-run with the same four questions.

**Expected outcomes** (your mileage will vary; small models are inconsistent on tool use):

- **Question 1**: May still answer "what is BGP?" reasonably from training.
- **Questions 2–4**: Often fail or partially fail. Common failure modes:
  - Doesn't call the tool when it should
  - Calls the tool but with wrong arguments (`node='router1'` instead of `node='r1'`)
  - Calls the tool, gets the answer, then ignores it and makes up an answer anyway
  - Loops calling the tool repeatedly without progress

**The lesson:** tool-calling is a capability that scales hard with model size. For agentic workflows, smaller local models are often not good enough. This matters for the "data sovereignty vs. capability" trade-off from the talk — if your task *needs* an agent, you probably need a bigger model, which constrains your hosting options.

Don't take this as "local LLMs are useless." It means: pick the right model for the job. Lab 1's local model was *great* for casual Q&A. Lab 3's local model is *struggling* with structured tool use. Same model, different task.

---

## Going Further

### 1. Add a second tool — `get_ospf_state`

Define an OSPF tool symmetric to the BGP one. Capture OSPF outputs from r1 and r2 (use `show network-instance default protocols ospf neighbor` in the SR Linux CLI), save to `sample_data/r1_ospf.txt` etc., and add a new `@tool` function. Re-run questions like:

- "How's OSPF doing on r1?" — should call only the OSPF tool
- "Is r1 fully converged with r2 on both BGP and OSPF?" — agent should call *both* tools and combine

> **Tip:** naming both protocols explicitly ("…on both BGP and OSPF") reliably nudges the agent to call both tools. A vaguer phrasing like "Is r1 fully converged with r2?" often makes the agent check only BGP — "converged" alone doesn't tell it OSPF is in scope. This is a good illustration of how much the *wording* of a request steers an agent's tool choices.

This is where having multiple tools starts to feel meaningfully agentic.

### 2. Add a `diagnose_session` tool

A second-step tool: `diagnose_session(node: str, peer_ip: str) -> str` that takes a specific peer and returns possible causes for the state it's in. The agent's behavior becomes multi-step:

1. Call `get_bgp_state('r1')` to discover the peers
2. Identify a peer in a problem state
3. Call `diagnose_session('r1', '10.1.13.2')` to get diagnosis details

Try: "Why isn't r3 receiving routes from r1?" — and watch the agent multi-step.

### 3. Push the live SSH into the tool itself

Step 5 showed that swapping canned files for fresh live captures works without touching the agent. The next step is making the tool *itself* live — no intermediate file. Install paramiko (`pip install paramiko` — already runs in the Codespace, not in the image), then:

```python
import paramiko

def fetch_bgp_live(node: str) -> str:
    """SSH to the node and capture BGP neighbor output."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=f"clab-autocon5-{node}",
        username="admin",
        password="NokiaSrl1!",
    )
    stdin, stdout, stderr = client.exec_command(
        "show network-instance default protocols bgp neighbor"
    )
    output = stdout.read().decode()
    client.close()
    return output
```

Then in `get_bgp_state`, try `fetch_bgp_live(node)` first, fall back to the file if it fails (e.g., containerlab not deployed). Now the tool is genuinely hybrid — live when available, canned otherwise.

### 4. Memory — agent that remembers the conversation

By default, each `executor.invoke()` is stateless. Use `ConversationBufferMemory` so follow-up questions work:

```python
from langchain.memory import ConversationBufferMemory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
```

Then a conversation like "show me r1's BGP" → "now show me r2" works without re-specifying context.

### 5. Custom personality / response style

Change the system prompt to give the agent a specific style — "respond as a CCIE instructor explaining to a junior engineer," or "answer in three bullet points," or "include only the facts, no commentary." Notice how the same agent with the same tools produces very different output. The system prompt is your most powerful steering tool.

---

## What's next

In **Lab 4 (Streamlit Frontend)**, you'll wrap this agent in a chat UI. Instead of running `python agent.py` and editing the question in the source code, your users will type questions into a web page and watch the agent's responses stream back in real time. The agent code stays exactly the same — you'll just put a face on it.
