"""agent.py — a tiny LangChain agent with one tool.

Demonstrates the agent loop across questions that exercise different behaviors:
  - General question (no tool call)
  - Single tool call
  - Tool call + reasoning over result
  - Multiple tool calls + synthesis
"""
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


# if __name__ == "__main__":
#     question = "What's BGP looking like on r1?"
#     print(f"\nQuestion: {question}\n{'=' * 60}")
#     result = executor.invoke({"input": question})
#     print(f"\n{'=' * 60}\nFinal answer:\n{result['output']}")

if __name__ == "__main__":
    questions = [
        "What is BGP?",                              # General — should not call any tool
        "What's BGP looking like on r1?",            # Specific — single tool call
        # "Is r3 peering with r1?",                    # Specific — needs reasoning over result
        # "Compare BGP state between r1 and r3.",      # Should call the tool twice
    ]

    for q in questions:
        print(f"\n{'=' * 70}\nQuestion: {q}\n{'=' * 70}")
        result = executor.invoke({"input": q})
        print(f"\nFinal answer:\n{result['output']}")
