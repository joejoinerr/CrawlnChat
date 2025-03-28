"""
MCP (Model Context Protocol) interface for Crawl n Chat.
"""

from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
from src.core.settings import (
    MCP_PORT,
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION,
    DEFAULT_EMBEDDING_MODEL,
)
from src.core.router import AgentRouter
from src.core import get_logger
from src.core.logger import configure_logging


logger = get_logger("mcp_app")


class RuntimeError(Exception):
    """
    Custom exception for MCP server runtime errors.
    """
    pass


# Global service instances
agent_router: Optional[AgentRouter] = None

# Create MCP server - explicitly set port
logger.info(f"Initializing MCP server with port {MCP_PORT}")

mcp = FastMCP(
    name=API_TITLE, description=API_DESCRIPTION, version=API_VERSION, port=MCP_PORT
)


# Add a tool to chat with content
@mcp.tool()
async def chat_with_content(query: str) -> Dict[str, Any]:
    """
    Chat with the crawled content by asking a question.

    Args:
        query: User query to be answered based on crawled content.

    Returns:
        Dictionary with AI answer and metadata.
    """
    global agent_router

    if not agent_router:
        return {"error": "Service not initialized"}

    try:
        result = await agent_router.process_query(query=query)
        return {"response": result["response"], "sources": result.get("sources", [])}
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return {"error": f"Error processing query: {str(e)}"}


def run_mcp_server(
    init_agent_router: AgentRouter = None,
) -> None:
    """
    Run the MCP server.

    Args:
        init_agent_router: Pre-initialized agent router instance.
    """
    global agent_router

    # Use provided instances or initialize new ones
    agent_router = (
        init_agent_router
        if init_agent_router
        else AgentRouter(embedding_model=DEFAULT_EMBEDDING_MODEL)
    )

    if not agent_router:
        raise RuntimeError(
            "Shared services must be initialized before starting the server"
        )

    try:
        # Set minimal logging when running MCP to prevent interference with JSON-RPC
        # Log messages are still written to the log file at the usual level
        configure_logging("CRITICAL")
        
        # Run the MCP server with stdio transport
        mcp.run(transport="stdio")


    except Exception as e:
        logger.error(f"MCP server failed to start or crashed: {e}")
        raise


if __name__ == "__main__":
    run_mcp_server()
