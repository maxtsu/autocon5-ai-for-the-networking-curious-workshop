# AutoCon 5: AI for the Networking Curious

> **Track B2 · Monday afternoon · 4 hours · hands-on**
> Eric Chou — Network to Code

This repo is the lab environment for the AC5 "AI for the Networking Curious" workshop. The whole stack — local LLM, network simulator, Python toolchain, chat GUI — runs in a GitHub Codespace you launch with one click. Nothing to install locally beyond a browser.

If you're here on workshop day, jump straight to [**Launch your Codespace**](#launch-your-codespace) below.

> **Tip:** hover over any code block in this README (or any lab README) for a copy button — saves you from selecting the text manually.

## What you'll build

Four labs, each building on the last:

1. **Hello LLMs** — your first calls to both a local LLM (Ollama, `llama3.2:3b`) and a cloud LLM (OpenAI `gpt-4o-mini`). See the trade-offs first-hand.
2. **Prompt Engineering** — go from "vibe prompting" to disciplined output: few-shot examples, Pydantic schemas, context injection to fight hallucinations.
3. **LangChain Network Agent** — wrap your prompting work as a tool, hand it to a LangChain agent, watch the agent reason about which tool to call and when.
4. **Streamlit Frontend** — put a chat UI on top of the agent. Your team can use it without ever touching Python.

By the end you've built a small but real "network co-pilot." Roughly 140 lines of code, four files, runs anywhere a Codespace can run.

## Prerequisites

Bring:

- A laptop with **Chrome** (recommended) or a recent Firefox/Edge
- A **GitHub account** — free tier is fine
- An **OpenAI account** with at least **$5 of prepaid credit** ([sign up here](https://platform.openai.com)). The account needs actual funded credit, not just a sign-up — Lab 1 will fail with a `RateLimitError` if there's no balance.

Have (we're not teaching these):

- Intermediate Python — read and edit a script, understand a class definition, run `python foo.py`
- Networking basics — BGP, OSPF, route tables. We use them as examples; we don't explain them.

See [WORKSHOP_FAQ.md](WORKSHOP_FAQ.md) for the full pre-workshop checklist.

## Launch your Codespace

1. Click the green **Code** button at the top of this page.
2. Switch to the **Codespaces** tab → **Create codespace on main**.
3. When prompted for machine type, pick **4-core / 16 GB / 32 GB** (the free tier). The 2-core tier doesn't have enough memory for SR Linux + Ollama + the rest of the stack.
4. Wait **5-8 minutes** for the first boot. The image is pulled once; subsequent restarts of the same Codespace are much faster.
5. When you see the **welcome banner** in the terminal (starts with `==================================================` and ends with sanity-check commands), you're ready. The banner confirms the SR Linux image loaded — that's how you know the Codespace finished setup successfully.
6. In VS Code's **Ports** panel (bottom of the screen), you should see two ports forwarded: 11434 (Ollama API, silent) and 8501 (Streamlit, opens later).
7. Start with [**Lab 1**](Lab_1_Hello_LLMs/README.md).

> **Want a snappier experience? (optional — GitHub Pro)** The default above is free and runs every lab. If you have GitHub Pro (or any plan that allows a larger machine), there's a second configuration — *"AutoCon 5 AI Workshop — GitHub Pro (larger machine)"* — that runs on an **8-core / 32 GB** machine (noticeably faster, especially Lab 3's live network sim + local LLM running together) and adds the **Open WebUI** chat GUI (Lab 1 Step 6). Pick it via **Codespaces → ⋯ → New with options…** → the **Dev container configuration** dropdown. Purely optional — the free default is fully sufficient.

## Workshop day — how we'll run the session

The Codespace takes 5–8 minutes to build on first boot, so on workshop day we'll start it right away and use the wait productively. Here's the opening sequence we'll do together:

1. **Everyone kick off your Codespace now.** Follow [Launch your Codespace](#launch-your-codespace) above. Don't just click and look away — watch that the build actually *starts*, then **click into the build log** (the "Building codespace…" / "View logs" link) to confirm it's making progress. If yours has stalled or errored, flag it now while we can fix it together, not 20 minutes in.
2. **No OpenAI account yet?** While the image builds, head to [platform.openai.com](https://platform.openai.com), create an account, and **add the $5 prepaid credit** (see [Prerequisites](#prerequisites) — Lab 1 fails without funded credit). Takes a couple of minutes; the build runs in the background.
3. **Optional — want to try Anthropic too?** If you'd like to compare Claude against OpenAI later (Lab 1's "Going further" #5), grab an Anthropic API key now at [console.anthropic.com](https://console.anthropic.com) — they include $5 in starter credits. Purely optional; OpenAI is all you need for the core labs.
4. **Still building?** Good — we'll start the **Lab 1 "Concepts" section** together while the image finishes. No need for a running Codespace to follow along with the concepts; by the time we reach the first hands-on step, your environment will be ready.

## A note on Codespaces billing

Short answer: **a 4-hour workshop on a free GitHub account does not cost you anything.**

Longer answer: GitHub gives every personal account ~120 core-hours of Codespace runtime per month, free. The 4-core machine we recommend uses 4 core-hours per actual hour of runtime, so a 4-hour workshop session burns ~16 core-hours — well inside the free allowance for most people. Storage is the same story: 15 GB free per month, our image is well under that.

That said: **stop your Codespace when you're done** to avoid leaving the meter running. GitHub UI → Codespaces → click the `...` next to yours → **Stop codespace**. (Or just close the browser tab; GitHub auto-stops after 30 min of inactivity by default.)

If you want a fresh environment for any reason, **delete** the Codespace instead of stopping it. Same menu, "Delete." Next launch pulls the image fresh.

## What's running inside the Codespace

When you boot, you get:

- **Python 3.11** with LangChain, OpenAI, Streamlit, Ollama, Pydantic, and the supporting libraries pre-installed
- **Ollama** with `llama3.2:3b` already pulled into the image — no model download needed at boot
- **Open WebUI** v0.9.5 — chat GUI for Ollama on port 8080 *(GitHub Pro image only; the default image uses the `ollama run` CLI instead)*
- **Containerlab** 0.74.3 for spinning up the network topology
- **SR Linux** 25.10.2 image baked in — three nodes (`r1`, `r2`, `r3`) running OSPF + iBGP + eBGP
- All the **lab content** — READMEs and pre-built Python scripts for each lab

## Topology

The topology you'll deploy in Labs 3-4:

```
            AS 65002 (external)
            ┌──────┐
            │  r3  │
            └───┬──┘
                │ eBGP (10.1.13.0/30)
            ┌───┴──┐                          ┌──────┐
            │  r1  │── OSPF + iBGP ────────── │  r2  │
            └──────┘                          └──────┘
                       AS 65001 (internal)
```

Three SR Linux nodes. `r1` and `r2` are in the same AS and run iBGP over a loopback session, with OSPF as the IGP underneath. `r3` is in a different AS and peers eBGP with `r1`. Realistic enough to demonstrate the patterns, small enough to fit in a Codespace.

## The labs, in order

| # | Lab | What you do | Time |
|---|-----|-------------|------|
| 1 | [Hello LLMs](Lab_1_Hello_LLMs/README.md) | First calls to Ollama and OpenAI; compare the two | ~25 min |
| 2 | [Prompt Engineering](Lab_2_Prompt_Engineering/README.md) | Four prompting techniques: naive, few-shot, structured, context-injected | ~25 min |
| 3 | [LangChain Network Agent](Lab_3_LangChain_Network_Agent/README.md) | Wrap a tool, build an agent, watch it reason | ~25 min |
| 4 | [Streamlit Frontend](Lab_4_Streamlit_Frontend/README.md) | Chat UI over the agent — your network co-pilot | ~25 min |

Bonus discussion topics (MCP, agents in production, real RAG, where this all goes next) if time allows.

## If something goes wrong

**The Codespace gets stuck at "88% — installing docker-in-docker"**
Common, harmless. Docker is usually already running by the time you see this. Open a new terminal in VS Code and run `docker info` — if you get version info back, the daemon is up and the progress dialog is just stale. Dismiss it.

**The welcome banner never appears**
postCreate.sh probably failed. Open the terminal panel, look for errors. The most common cause is a transient image-load failure — run `docker images` to check whether SR Linux loaded (and Open WebUI too, if you're on the GitHub Pro image).

**(GitHub Pro image) Open WebUI shows up but the model dropdown is empty**
Ollama isn't running yet. In any terminal: `ollama serve > /tmp/ollama.log 2>&1 &`, then refresh the Open WebUI page. (Lab 1 covers this explicitly — feel free to skip ahead to that step if it's bothering you.) On the default image there's no Open WebUI — chat from the CLI with `ollama run llama3.2:3b`.

**Streamlit pages fail to render in VS Code's Simple Browser**
Open the forwarded port in a *real* browser instead: in the Ports panel, click the globe icon next to port 8501. Simple Browser's sandboxing breaks Streamlit's WebSocket connection; a real browser tab works fine.

**`containerlab deploy` fails with "User 'vscode' is not part of containerlab admin group"**
That group membership is baked into the image, so this shouldn't happen on a fresh Codespace. If it does, run `sudo usermod -aG clab_admins vscode && newgrp clab_admins` and retry.

**After `containerlab deploy`, r3's BGP neighbor table is empty**
Known issue with SR Linux 25.10's bulk startup-config push — one neighbor line on r3 gets silently dropped. Apply the live fix on r3:
```
ssh admin@clab-autocon5-r3    # password: NokiaSrl1!
enter candidate
set / network-instance default protocols bgp neighbor 10.1.13.1 peer-group ebgp-r1
commit now
quit
```
Lab 3 Step 5 walks through this in context — feel free to skip ahead to that step if it's bothering you.

**OpenAI calls fail with `AuthenticationError`**
Your API key isn't loading. Open `.env` in the file explorer and confirm `OPENAI_API_KEY=sk-...` is there, with no quotes or trailing spaces.

**OpenAI calls fail with `RateLimitError` / "insufficient quota"**
Your key is valid but the account has no credit. Add at least $5 at [platform.openai.com/settings/organization/billing](https://platform.openai.com/settings/organization/billing).

**Nothing above helps — start fresh**
Delete the Codespace (GitHub UI → `...` → Delete) and create a new one. The image is built to be reproducible — a fresh Codespace is the cheapest test of "is the problem me or my environment."

## Getting help

- **During the workshop:** raise a hand. Proctors are in the room.
- **After the workshop:** open an issue on this repo, or find me on the AutoCon Slack.

## License

Apache 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).

By Eric Chou — Copyright 2026 Network to Code, LLC.
