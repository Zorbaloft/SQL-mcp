"""MCP tool definitions for MySQL database exploration."""

import re
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .database import ReadOnlyError, get_db_manager

mcp = FastMCP("mysql-database")


@mcp.tool()
def list_databases() -> List[str]:
    """
    List all available databases in the MySQL server.

    Returns:
        List of database names
    """
    db = get_db_manager()
    return db.list_databases()


@mcp.tool()
def list_tables(database: str) -> List[Dict[str, str]]:
    """
    List all tables and views in a specific database.

    Args:
        database: Name of the database to query

    Returns:
        List of dictionaries with 'name', 'type' (TABLE/VIEW), and 'comment' fields
    """
    db = get_db_manager()
    try:
        return db.list_tables(database)
    except Exception as e:
        return [{'error': f"Failed to list tables: {str(e)}"}]


@mcp.tool()
def describe_table(database: str, table: str) -> Dict[str, Any]:
    """
    Get detailed structure of a table including columns, types, and constraints.

    Args:
        database: Name of the database
        table: Name of the table

    Returns:
        Dictionary containing table metadata, comment, and column details
    """
    db = get_db_manager()
    try:
        return db.describe_table(database, table)
    except Exception as e:
        return {'error': f"Failed to describe table: {str(e)}"}


@mcp.tool()
def list_indexes(database: str, table: str) -> List[Dict[str, Any]]:
    """
    List all indexes for a specific table.

    Args:
        database: Name of the database
        table: Name of the table

    Returns:
        List of index definitions with name, columns, type, and uniqueness
    """
    db = get_db_manager()
    return db.list_indexes(database, table)


@mcp.tool()
def list_foreign_keys(database: str, table: str) -> List[Dict[str, Any]]:
    """
    List foreign key relationships for a table.

    Args:
        database: Name of the database
        table: Name of the table

    Returns:
        List of foreign key relationships with referenced tables and columns
    """
    db = get_db_manager()
    return db.list_foreign_keys(database, table)


@mcp.tool()
def get_view_definition(database: str, view: str) -> Optional[str]:
    """
    Get the SQL definition of a view.

    Args:
        database: Name of the database
        view: Name of the view

    Returns:
        SQL definition string or None if view not found
    """
    db = get_db_manager()
    return db.get_view_definition(database, view)


@mcp.tool()
def get_table_comments(database: str) -> List[Dict[str, Any]]:
    """
    Get comments and metadata for all tables in a database.

    Args:
        database: Name of the database

    Returns:
        List of table metadata including names and comments
    """
    db = get_db_manager()
    tables = db.list_tables(database)
    result = []
    for table in tables:
        table_info = db.describe_table(database, table['name'])
        result.append({
            'name': table['name'],
            'type': table['type'],
            'comment': table_info.get('comment'),
            'column_count': len(table_info.get('columns', [])),
        })
    return result


@mcp.tool()
def execute_query(query: str, limit: int = 1000) -> Dict[str, Any]:
    """
    Execute a read-only SQL query safely.

    Args:
        query: SQL SELECT query to execute
        limit: Maximum number of rows to return (default: 1000, max: 1000)

    Returns:
        Dictionary with 'rows' (list of result rows) and 'count' (number of rows)
    """
    db = get_db_manager()
    if limit > 1000:
        limit = 1000

    # Check if LIMIT already exists at the end of the query (simple check)
    # Note: This won't catch LIMIT in subqueries, but prevents double LIMIT
    query_stripped = query.strip().rstrip(';')
    query_upper = query_stripped.upper()
    
    # Only add LIMIT if query doesn't end with LIMIT clause
    if not query_upper.rstrip().endswith('LIMIT'):
        # Check if LIMIT is already present (simple pattern match)
        if not re.search(r'\bLIMIT\s+\d+', query_upper, re.IGNORECASE):
            query = f"{query_stripped} LIMIT {limit}"
        else:
            query = query_stripped
    else:
        query = query_stripped

    try:
        rows = db.execute_query(query)
        return {
            'rows': rows,
            'count': len(rows),
        }
    except ReadOnlyError as e:
        return {
            'error': str(e),
            'rows': [],
            'count': 0,
        }
    except Exception as e:
        return {
            'error': f"Query execution failed: {str(e)}",
            'rows': [],
            'count': 0,
        }


@mcp.tool()
def sample_data(database: str, table: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Sample rows from a table for inspection.

    Args:
        database: Name of the database
        table: Name of the table
        limit: Number of rows to sample (default: 100, max: 1000)

    Returns:
        List of sample rows as dictionaries
    """
    db = get_db_manager()
    return db.sample_data(database, table, limit)


@mcp.tool()
def get_schema_metadata(database: str) -> Dict[str, Any]:
    """
    Get comprehensive metadata for an entire database schema.

    Args:
        database: Name of the database

    Returns:
        Dictionary containing tables, views, relationships, and metadata summary
    """
    db = get_db_manager()
    tables = db.list_tables(database)

    schema_info = {
        'database': database,
        'tables': [],
        'views': [],
        'total_tables': 0,
        'total_views': 0,
    }

    for table in tables:
        table_name = table['name']
        table_type = table['type']

        if table_type == 'VIEW':
            view_def = db.get_view_definition(database, table_name)
            schema_info['views'].append({
                'name': table_name,
                'comment': table['comment'],
                'definition': view_def,
            })
            schema_info['total_views'] += 1
        else:
            table_desc = db.describe_table(database, table_name)
            indexes = db.list_indexes(database, table_name)
            foreign_keys = db.list_foreign_keys(database, table_name)

            schema_info['tables'].append({
                'name': table_name,
                'comment': table_desc.get('comment'),
                'column_count': len(table_desc.get('columns', [])),
                'index_count': len(set(idx['name'] for idx in indexes)),
                'foreign_key_count': len(foreign_keys),
            })
            schema_info['total_tables'] += 1

    return schema_info
