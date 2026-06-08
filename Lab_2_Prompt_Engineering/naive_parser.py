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