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
