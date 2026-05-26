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
