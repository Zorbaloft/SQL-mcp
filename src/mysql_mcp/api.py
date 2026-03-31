"""REST API endpoints for the MySQL MCP server frontend."""

import json
from typing import Any, Dict, List, Optional
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.requests import Request

from .database import ReadOnlyError, get_db_manager
from .tools import (
    list_databases as tool_list_databases,
    list_tables as tool_list_tables,
    describe_table as tool_describe_table,
    list_indexes as tool_list_indexes,
    list_foreign_keys as tool_list_foreign_keys,
    get_view_definition as tool_get_view_definition,
    get_table_comments as tool_get_table_comments,
    execute_query as tool_execute_query,
    sample_data as tool_sample_data,
    get_schema_metadata as tool_get_schema_metadata,
)


async def get_databases(request: Request):
    """List all databases."""
    try:
        result = tool_list_databases()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def get_tables(request: Request):
    """List tables in a database."""
    database = request.path_params["database"]
    try:
        result = tool_list_tables(database)
        if result and isinstance(result[0], dict) and "error" in result[0]:
            return JSONResponse({"error": result[0]["error"]}, status_code=404)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def get_table_structure(request: Request):
    """Get table structure."""
    database = request.path_params["database"]
    table = request.path_params["table"]
    try:
        result = tool_describe_table(database, table)
        if isinstance(result, dict) and "error" in result:
            return JSONResponse({"error": result["error"]}, status_code=404)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def get_table_indexes(request: Request):
    """Get table indexes."""
    database = request.path_params["database"]
    table = request.path_params["table"]
    try:
        result = tool_list_indexes(database, table)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def get_table_foreign_keys(request: Request):
    """Get table foreign keys."""
    database = request.path_params["database"]
    table = request.path_params["table"]
    try:
        result = tool_list_foreign_keys(database, table)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def get_table_sample(request: Request):
    """Sample data from a table."""
    database = request.path_params["database"]
    table = request.path_params["table"]
    limit = int(request.query_params.get("limit", 100))
    limit = max(1, min(1000, limit))
    try:
        result = tool_sample_data(database, table, limit)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def execute_sql_query(request: Request):
    """Execute a read-only SQL query."""
    try:
        body = await request.json()
        query = body.get("query", "")
        limit = body.get("limit", 1000)
        result = tool_execute_query(query, limit)
        if "error" in result:
            return JSONResponse(result, status_code=400)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def get_database_metadata(request: Request):
    """Get complete database metadata."""
    database = request.path_params["database"]
    try:
        result = tool_get_schema_metadata(database)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def get_routes():
    """Get API routes for mounting."""
    return [
        Route("/api/databases", get_databases, methods=["GET"]),
        Route("/api/databases/{database}/tables", get_tables, methods=["GET"]),
        Route("/api/databases/{database}/tables/{table}", get_table_structure, methods=["GET"]),
        Route("/api/databases/{database}/tables/{table}/indexes", get_table_indexes, methods=["GET"]),
        Route("/api/databases/{database}/tables/{table}/foreign-keys", get_table_foreign_keys, methods=["GET"]),
        Route("/api/databases/{database}/tables/{table}/sample", get_table_sample, methods=["GET"]),
        Route("/api/query", execute_sql_query, methods=["POST"]),
        Route("/api/databases/{database}/metadata", get_database_metadata, methods=["GET"]),
    ]
