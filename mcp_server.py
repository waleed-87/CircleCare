from mcp.server.fastmcp import FastMCP

mcp = FastMCP("carecircle")


@mcp.tool()
def ping() -> str:
    """Check that the server works."""
    return "pong"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")