"""Fast MCP server entry point for MySQL read-only database exploration."""

import os
import sys
from pathlib import Path

# Add src to path for imports (works both in Docker and local dev)
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from starlette.middleware.cors import CORSMiddleware
from mysql_mcp.tools import mcp
from mysql_mcp.api import get_routes


def main():
    """Run the MCP server."""
    # Load environment variables if .env exists (for local development)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Validate required environment variables
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD']
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    # Add CORS middleware
    mcp.app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add API routes
    for route in get_routes():
        mcp.app.routes.append(route)
    
    # Run the MCP server with SSE transport
    # FastMCP SSE uses uvicorn under the hood
    # Get port from environment variable, default to 8001
    port = int(os.getenv("PORT", os.getenv("UVICORN_PORT", "8001")))
    host = os.getenv("UVICORN_HOST", "0.0.0.0")
    
    # Explicitly bind to 0.0.0.0 to allow connections from outside the container
    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()
