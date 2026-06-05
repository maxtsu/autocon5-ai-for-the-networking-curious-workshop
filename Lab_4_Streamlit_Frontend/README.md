# Lab 4: Streamlit Frontend — Putting a Face on Your Agent

**Time:** ~25 minutes

Take the agent from Lab 3 and wrap it in a chat web app. By the end, instead of running `python agent.py` and editing the source code to change your question, you'll have a real web UI at `localhost:8501` where anyone can type a question and get a streamed response back — no Python required to *use* the tool, only to build it.

This is the visual capstone of the workshop. The agent code from Lab 3 stays exactly the same. Lab 4 is purely about presentation.

## Prerequisites

- Lab 3 completed (the `bgp_tool.py` and sample data from Lab 3 are required — Lab 4 reuses them).
- Basic familiarity with Python imports (we'll cross-reference files between lab folders).

## Concepts

- **Streamlit's rerun model.** Every interaction (button click, text input, etc.) reruns your script from the top. This feels weird at first but means your UI is always a pure function of state — no event handlers, no callbacks. Just read state, render.
- **Session state.** Because the script reruns, regular Python variables get reset. `st.session_state` is the dictionary that persists across reruns — that's where chat history lives.
- **`st.chat_input` and `st.chat_message`.** Streamlit ships with chat-specific components. You don't have to build the UI primitives; they're already styled to match what people expect from a chat app.
- **Why wrap an agent in a UI at all.** A Python script is fine for engineers comfortable with Python. A web UI is for everyone else on your team. The agent's *capability* doesn't change; its *accessibility* does. That's a meaningful product decision in real network teams.

---

## Step 1: Streamlit "hello world"

Before we add complexity, just get something rendering. Create `hello.py` in this lab folder:

```python
"""hello.py — minimal Streamlit app to verify the setup."""
import streamlit as st

st.title("Network Co-Pilot")
st.write("If you can see this, Streamlit is working.")

name = st.text_input("What's your name?")
if name:
    st.write(f"Hello, {name}!")
```

Run it:

```bash
cd /workspaces/autocon5-ai-workshop
streamlit run Lab_4_Streamlit_Frontend/hello.py
```

**Expected:** Streamlit prints two URLs in the terminal (a local and a network URL), and VS Code's Ports panel will auto-open a preview of port **8501** labeled "Streamlit."

> **Important — prefer a real browser over Simple Browser.** The auto-opened preview pane in VS Code is its built-in "Simple Browser," whose sandboxing often breaks Streamlit's WebSocket connection. The page renders, but interactions may silently stop working (typing into inputs, button clicks, chat messages). It works for some setups and not others — so to be safe, in the **Ports panel** click the **globe icon** next to port 8501 to open the app in your real browser (Chrome/Firefox/Edge). If anything in the UI seems dead, switching to a real browser is the first thing to try. **This applies to every `streamlit run` in this lab.**

In the browser tab, type your name. You should see "Hello, ..." appear below as you type.

> **Streamlit's rerun model, in action:** every keystroke in the text input reruns `hello.py` from the top. The first time through, `name` is empty and `if name:` is False. After you type a character, `name` is your input and the conditional renders. It looks like reactivity, but it's actually re-execution — a simpler model with the same end result.

To stop the app: `Ctrl+C` in the terminal.

---

## Step 2: A static chat layout

> **Heads up — this file is already in the repo, in its finished form.** `chat_app.py` is here in this lab folder as a reference starting point — and the version on disk is the *final* app (the end state of Step 5), not the static layout shown in this step. Steps 2–4 build it up incrementally, so if you run the on-disk file right now you'll get the full agent-backed app, not this static mock. Read along with the snippets here to follow the progression, or, for the challenge, delete the file and build it up yourself step by step.

Now let's build the chat UI shape without any LLM behind it yet. Here's the starting point for `chat_app.py`:

```python
"""chat_app.py — static chat UI, no agent yet."""
import streamlit as st

st.title("Network Co-Pilot")
st.caption("Ask questions about the lab topology.")

# Hardcoded conversation, just to see the chat layout
messages = [
    {"role": "user",      "content": "What's BGP looking like on r1?"},
    {"role": "assistant", "content": "r1 has two BGP neighbors, both established."},
    {"role": "user",      "content": "Is r3 peering with r1?"},
    {"role": "assistant", "content": "Yes — r1 has an eBGP session with r3 in AS 65002."},
]

for msg in messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input bar at the bottom (doesn't do anything yet)
prompt = st.chat_input("Ask me about your network...")
if prompt:
    st.write(f"You asked: {prompt}")
```

Run it:

```bash
streamlit run Lab_4_Streamlit_Frontend/chat_app.py
```

**Expected:** A chat-styled view with the four hardcoded messages — user messages on one side, assistant on the other, each in a chat bubble with an avatar. At the bottom, a chat input field. Typing into it just echoes "You asked: ..." for now.

Two things to notice:

- `st.chat_message("user")` and `st.chat_message("assistant")` automatically style with the right avatars and alignment — you get the ChatGPT look for free.
- `st.chat_input(...)` is *always pinned to the bottom* of the page, like a real chat app. Returns the typed value when the user hits Enter.

---

## Step 3: Persistent chat history with session state

The script reruns on every input, which means our `messages` list gets reset. To persist conversation across turns, we use `st.session_state`. Update `chat_app.py`:

```python
"""chat_app.py — chat UI with persistent history (session state)."""
import streamlit as st

st.title("Network Co-Pilot")
st.caption("Ask questions about the lab topology.")

# Initialize chat history on first run
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render every message in history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Handle new input
if prompt := st.chat_input("Ask me about your network..."):
    # Add the user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Render it immediately (next rerun will also render it from history)
    with st.chat_message("user"):
        st.write(prompt)

    # Generate a placeholder response (we'll replace this with the agent in Step 4)
    response = f"You said: {prompt}"
    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.write(response)
```

Re-run (Streamlit auto-reloads when you save; or restart manually).

**Expected:** Type three questions. All six messages (3 user, 3 assistant) stay in the chat as you continue typing. The conversation builds up. Refresh the page — history clears (session state is per-browser-session).

Two patterns worth memorizing from this code:

- `:=` walrus operator with `st.chat_input(...)`: returns the value if the user submitted, `None` otherwise. The whole `if prompt := ...` block runs only when there's new input.
- After appending to `st.session_state.messages`, we *also* render the new messages with `st.chat_message`. Why? Because the script already ran past the rendering loop above before we appended. Rendering immediately gives users instant feedback rather than waiting for the next rerun.

---

## Step 4: Wire in the Lab 3 agent

Now replace `f"You said: {prompt}"` with a real call to the agent. Update `chat_app.py`:

```python
"""chat_app.py — chat UI backed by the Lab 3 network agent."""
import sys
from pathlib import Path
import streamlit as st
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Import the BGP tool from Lab 3. We add Lab 3's folder to the import path
# so this stays a single self-contained file.
LAB3_DIR = Path(__file__).parent.parent / "Lab_3_LangChain_Network_Agent"
sys.path.insert(0, str(LAB3_DIR))
from bgp_tool import get_bgp_state  # noqa: E402


@st.cache_resource
def build_agent():
    """Build the agent once and cache it across reruns.

    @st.cache_resource is the right pattern for "expensive things you build
    once" — DB connections, model handles, LangChain agents. Without caching,
    Streamlit would rebuild this on every single rerun (every keystroke).
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a network engineering assistant for a small containerlab "
         "topology with three nodes: r1, r2, r3. Use tools when the user asks "
         "about specific routers. For general concept questions, answer from "
         "your own knowledge without calling tools."),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    tools = [get_bgp_state]
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


agent = build_agent()

# ---------- UI ----------

st.title("Network Co-Pilot")
st.caption("Ask questions about the lab topology (r1, r2, r3).")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask me about your network..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = agent.invoke({"input": prompt})
        st.write(result["output"])

    st.session_state.messages.append({"role": "assistant", "content": result["output"]})
```

Re-run. Try these questions in order:

- *"What is BGP?"* — Agent should answer from knowledge without calling the tool.
- *"What's BGP looking like on r1?"* — Agent calls `get_bgp_state('r1')`, then summarizes.
- *"Is r3 peering with r1?"* — Agent calls the tool for r3 and reasons over the result.
- *"Compare r1 and r3."* — Agent should call the tool twice.

**Expected:** Same kinds of responses you saw in Lab 3, but now in a chat UI. The terminal where you ran `streamlit run` shows the verbose agent trace — tool calls, intermediate observations — so you can watch the agent reason while users only see the polished final answer.

> **Notice the `{chat_history}` placeholder in the prompt template.** It's there on purpose, but this version doesn't fill it yet — each turn is sent to the agent on its own, so a bare follow-up like *"and r3?"* (with no router named) won't reliably resolve against the previous turn. Wiring history in is a small, optional upgrade — see **Going Further → "Make it conversational"** below.

> **About `@st.cache_resource`:** Streamlit reruns your entire script on every interaction. Without caching, you'd be rebuilding the agent (which compiles tool descriptions, sets up the LLM client, etc.) on every keystroke. `@st.cache_resource` tells Streamlit "this object is expensive and reusable — keep it around." It's the same pattern as a module-level singleton in regular Python, but Streamlit-aware.

---

## Step 5: Polish — title, clear button, and try it

Final touches to make it feel finished. Update `chat_app.py`'s UI section:

```python
# ---------- UI ----------

st.set_page_config(page_title="Network Co-Pilot", page_icon="🌐", layout="centered")

st.title("🌐 Network Co-Pilot")
st.caption("Ask questions about the lab topology — r1, r2, r3. The assistant uses tools to inspect BGP state.")

# Sidebar with controls
with st.sidebar:
    st.markdown("### Controls")
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("### Try asking")
    st.markdown(
        "- *What is BGP?*\n"
        "- *What's BGP looking like on r1?*\n"
        "- *Compare r1 and r3.*\n"
        "- *Is r3 peering with r1?*\n"
    )

    st.markdown("### About")
    st.caption("AutoCon 5 demo — uses canned BGP data from Lab 3's `sample_data/`.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# ... rest unchanged
```

Re-run. You should now see:

- A page title and emoji icon in the browser tab
- A sidebar with a clear button, suggested questions, and an "About" caption
- The main chat takes the centered area

Hit "Clear conversation" → history resets, conversation restarts. Try the suggested questions one by one to make sure everything's wired up.

**That's the app.** It's roughly 60 lines of Streamlit code, calling into roughly 40 lines of agent code, calling into roughly 40 lines of parser code from Lab 2 — about 140 lines total of substantive work to go from "I want to ask an LLM about my network" to "I have a chat web app my whole team can use."

> **A generic chat GUI like Open WebUI** (which ships on the GitHub Pro image) does basically the same thing for general chat — UI on top of a model. The difference: Open WebUI is generic (any prompt, any model), and what you just built is *purpose-specific* (your tools, your topology, your prompt). Both are valid; both have their place.

---

## Going Further

If you finish the core lab early — or want to extend it later:

### 1. Config generator app — the human-in-the-loop pattern

Instead of *querying* the network, generate *configs* from natural-language intent, with explicit human review before anything would touch a device. This is the most workshop-relevant pattern given the talk's emphasis on guardrails.

> **Heads up — this file is already in the repo.** `config_gen.py` is here in this lab folder as a reference starting point. Open it and follow along, or, if you want the challenge, delete it and write it yourself from the steps. Either way works.

Here's `config_gen.py`:

```python
"""config_gen.py — intent → SR Linux config, with human-in-the-loop review."""
import streamlit as st
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="SR Linux Config Generator", page_icon="🛠️")
st.title("🛠️ SR Linux Config Generator")
st.caption("Describe what you want; review the generated config before applying.")

intent = st.text_area("What do you want to configure?",
                       placeholder="e.g., Add an eBGP neighbor 10.0.99.1 in AS 65010 with permit-all policies")

if "generated_config" not in st.session_state:
    st.session_state.generated_config = None

if st.button("Generate config", type="primary"):
    if not intent.strip():
        st.error("Describe what you want to configure first.")
    else:
        with st.spinner("Generating..."):
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            prompt = (
                "You are an SR Linux configuration expert. Generate config "
                "for the following intent. Use 'set / ...' syntax. Output "
                "ONLY the configuration commands, one per line, no commentary "
                "or markdown.\n\n"
                f"Intent: {intent}"
            )
            response = llm.invoke(prompt)
            st.session_state.generated_config = response.content

if st.session_state.generated_config:
    st.markdown("### Review the generated config")
    st.code(st.session_state.generated_config, language="bash")

    col_left, col_right = st.columns(2)
    with col_left:
        if st.button("✅ Approve & copy"):
            st.success("Approved. In production, this would be the point at which "
                       "the config is pushed to the device. For safety, this demo "
                       "stops here — copy the commands above and review on the box.")
    with col_right:
        if st.button("❌ Reject"):
            st.session_state.generated_config = None
            st.rerun()
```

Run with `streamlit run Lab_4_Streamlit_Frontend/config_gen.py`. Type an intent ("Add a BGP neighbor 10.0.99.1 in AS 65010"). The app generates SR Linux config, shows it for review, and offers approve/reject buttons. **Note that the "approve" button does nothing destructive** — that's the point. The human is the safety gate. A real production version would call SR Linux's JSON-RPC at that point; this demo deliberately stops short.

### 2. Stream responses token-by-token

Replace the `result = agent.invoke(...)` block with streaming. Streamlit ships `st.write_stream` which accepts a generator:

```python
def stream_response(prompt):
    for chunk in agent.stream({"input": prompt}):
        if "output" in chunk:
            yield chunk["output"]

with st.chat_message("assistant"):
    response = st.write_stream(stream_response(prompt))

st.session_state.messages.append({"role": "assistant", "content": response})
```

Note: `agent.stream(...)` yields events (steps, tool calls, then the final output). The simplest case shown above streams only the final answer. For full intermediate-step streaming, look at LangChain's `astream_events`.

### 3. Show the agent's reasoning steps in the UI

Add an expander that shows the tool calls the agent made:

```python
result = agent.invoke({"input": prompt}, return_intermediate_steps=True)

with st.chat_message("assistant"):
    st.write(result["output"])
    if result.get("intermediate_steps"):
        with st.expander("Show agent reasoning"):
            for action, observation in result["intermediate_steps"]:
                st.markdown(f"**Tool:** `{action.tool}` with `{action.tool_input}`")
                st.markdown(f"**Observation:** {observation}")
```

This is the "transparency layer" attendees often want — users can see *why* the agent gave the answer it did, not just *what* the answer was.

### 4. Make it conversational — fill the `{chat_history}` placeholder

The prompt template already has a `{chat_history}` placeholder, but the base app never fills it, so each turn is an island — a bare follow-up like *"and r3?"* doesn't resolve against the previous question. Wiring history in is a small change: on each turn, snapshot the prior messages (before appending the new one, so the current prompt isn't duplicated), convert them to LangChain message objects, and pass them as `chat_history`.

```python
from langchain_core.messages import HumanMessage, AIMessage   # add with the other imports

# ...inside the `if prompt := st.chat_input(...)` block, BEFORE appending the new message:
chat_history = [
    HumanMessage(content=m["content"]) if m["role"] == "user"
    else AIMessage(content=m["content"])
    for m in st.session_state.messages
]
# ...then pass it into the agent:
result = agent.invoke({"input": prompt, "chat_history": chat_history})
```

Now *"and r3?"* after asking about r1 works as a real follow-up. This snapshot resends the *entire* conversation every turn, though, which eventually overflows the model's token budget — so for long sessions, swap it for one of LangChain's memory helpers: `ConversationBufferWindowMemory` (keep only the last *k* turns) or `ConversationSummaryMemory` (summarize older turns instead of resending them verbatim).

### 5. Multi-page app

Streamlit supports multiple pages via a `pages/` folder. You could ship the chat UI as `app.py` and the config generator as `pages/config_gen.py`. Streamlit auto-builds the navigation. Useful for shipping a "co-pilot suite" rather than a single tool.

### 6. Deploy publicly

Streamlit Community Cloud lets you publish a public app from a GitHub repo for free. Push your Lab 4 code to a public repo, sign up at [share.streamlit.io](https://share.streamlit.io), and point it at the repo. You'd need to use Streamlit's secrets manager for the OpenAI API key (don't commit `.env`). The result: a public URL you can share with anyone.

---

## What's next — beyond this workshop

You've now built every layer of the AI-augmented network engineering stack: LLM access (Lab 1), prompt discipline (Lab 2), agents with tools (Lab 3), and a usable UI (Lab 4). Each piece is small. Together, they form a real production pattern.

Where to take it from here:

- **Real RAG** with vector stores (Chroma, FAISS) for richer reference data than inline `BGP_REFERENCE`.
- **MCP** (Model Context Protocol) — the emerging standard for connecting LLMs to external tools and data, more powerful than ad-hoc tool wiring.
- **Production deployment** — moving from Codespace to a container in your team's infrastructure, with proper secret management, observability, and access control.
- **Evals** — automated tests that measure your agent's accuracy on a fixed set of questions, so you can confidently update prompts or swap models without regressing.

The thread running through all of these: **disciplined engineering with guardrails**, exactly the framing from the AC5 talk. Vibe-coded prompts get you a demo. Schemas, agents, human-in-the-loop, and evals get you something that runs reliably in production.