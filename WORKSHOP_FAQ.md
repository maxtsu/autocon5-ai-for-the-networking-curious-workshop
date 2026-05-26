# Workshop FAQ — AI for the Networking Curious

*Track B2 · Monday afternoon · AutoCon 5*

Quick answers to questions I get a lot before this kind of workshop. Short version: bring a laptop, a GitHub account, and an OpenAI account with $5 of credit. That's it.

---

**Do I need to install anything beforehand?**

Almost nothing. The whole workshop runs inside a GitHub Codespace — a cloud-based dev environment — so you don't need Docker, Python, or any of the AI tools installed locally. Just a modern browser (Chrome works best) and your laptop's terminal.

---

**I'll need a GitHub account, right?**

Yes. Free tier is fine. Sign up at [github.com](https://github.com) if you don't have one — takes two minutes.

---

**Will GitHub Codespaces cost me anything?**

The free tier includes **120 core-hours and 15 GB-month of storage** — way more than a 4-hour workshop needs.

**Heads up though:** if you've already used Codespaces a lot this month for other projects, you might be close to your limit. Two minutes of homework before the workshop:

1. Check your usage at [github.com/settings/billing/summary](https://github.com/settings/billing/summary)
2. Stop any unused Codespaces if you're getting close

If you do hit the limit mid-workshop, paying a small overage (~$0.18/hour for a 4-core machine) keeps you running. Or use a different GitHub account.

---

**Which cloud LLM provider do I need an account with?**

**OpenAI.** Sign up at [platform.openai.com](https://platform.openai.com) and add **$5 USD** as prepaid credit before the workshop.

$5 is plenty — you'll likely spend under $0.50 during the lab. Whatever's left doesn't expire and is yours to use for anything else later.

If you can't add credit for some reason, flag it to me at the workshop — I have a backup key for emergencies, but bringing your own is strongly preferred.

---

**Why OpenAI and not Anthropic, Google, or someone else?**

All of those are excellent. We're using OpenAI for two practical reasons:

1. **Integrated fine-tuning.** OpenAI lets you fine-tune their models directly through their own platform — we'll cover fine-tuning as a bonus topic if time allows. Some other providers (Anthropic, for instance) require routing through AWS Bedrock to fine-tune, which adds significant setup overhead that wouldn't fit in our 4-hour window.

2. **Familiarity.** Most attendees have already used ChatGPT, so account setup is fast and the API mental model is comfortable.

The recipes we build are provider-agnostic — once the workshop is over, swapping in Claude, Gemini, or a local model is a one-line change in the LangChain code.

---

**Can I keep working on this after the workshop?**

Yes — that's one of the best parts of the Codespaces setup. The workshop repo is public, you can re-launch a fresh Codespace anytime (subject to your free quota), and everything we build together is yours to take back to your day job. You should leave with a working AI-augmented networking toolkit you can use Monday morning.

---

**How much Python and networking do I need to know?**

- **Python**: intermediate enough to read and edit a script. You don't need to be a developer.
- **Networking**: comfortable with the basics — BGP, OSPF, route tables, what a `show` command output looks like. We're not teaching networking; we're teaching how AI helps with the networking work you already do.

---

**What if I get stuck?**

Raise a hand — there'll be helpers in the room. We'll also have a Slack channel for pre-workshop questions and post-workshop follow-up; details will go out via the AutoCon 5 app.

---

**What if my company blocks GitHub or OpenAI?**

Best to do this workshop on a personal device or via the venue WiFi. Some corporate networks block Codespaces or external AI APIs — if yours does, your personal laptop on conference WiFi is the right move.

---

**Anything else I should bring?**

Just curiosity. And maybe a charger.

See you Monday afternoon.

— Eric