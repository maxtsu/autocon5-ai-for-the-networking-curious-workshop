"""bgp_server.py — minimal MCP server exposing the Lab 3 BGP data."""
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("network-tools")

# Reuse the sample data from Lab 3
SAMPLE_DATA = (
    Path(__file__).parent.parent.parent
    / "Lab_3_LangChain_Network_Agent"
    / "sample_data"
)


@mcp.tool()
def get_bgp_state(node: str) -> str:
    """Get the BGP peering state for a node in the topology.

    Args:
        node: Node name. One of: 'r1', 'r2', 'r3'.

    Returns:
        Raw show-command output for the node's BGP neighbors.
    """
    sample_file = SAMPLE_DATA / f"{node}_bgp.txt"
    if not sample_file.exists():
        return f"No BGP data for '{node}'. Available nodes: r1, r2, r3."
    return sample_file.read_text()


if __name__ == "__main__":
    mcp.run()  # defaults to stdio transport
