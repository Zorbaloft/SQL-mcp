# MySQL MCP Server

A read-only MySQL 8 MCP (Model Context Protocol) server built with Fast MCP, designed for database exploration, documentation, and safe querying.

## Features

- **Read-only by design**: Enforces read-only access at multiple levels
- **Comprehensive metadata**: Explore databases, tables, views, indexes, and relationships
- **Safe query execution**: Execute read-only SQL queries with automatic safety checks
- **Structured outputs**: JSON-formatted responses suitable for documentation generation
- **Dockerized**: Easy deployment with Docker and docker-compose
- **SSE support**: Compatible with Cursor MCP settings via Server-Sent Events
- **Modern Web UI**: Vue 3 + shadcn-vue frontend for database exploration

## Prerequisites

- Docker and Docker Compose
- MySQL 8+ database (accessible from the container)
- Python 3.10+ (for local development)

## Quick Start

### Using Docker Compose

1. **Clone or navigate to this directory**

2. **Create a `.env` file** (optional, for local development):
   ```env
   DB_HOST=your-mysql-host
   DB_PORT=3306
   DB_NAME=your-database
   DB_USER=your-username
   DB_PASSWORD=your-password
   PORT=8001
   ```

3. **Run with docker-compose**:
   ```bash
   docker-compose up -d
   ```

4. **Access the web UI**:
   - Frontend: http://localhost:3000
   - API: http://localhost:8001/api

5. **Verify the server is running**:
   ```bash
   docker-compose logs mysql-mcp
   ```

### Manual Docker Build

```bash
docker build -t mysql-mcp .
docker run -d \
  -p 8001:8001 \
  -e DB_HOST=your-host \
  -e DB_PORT=3306 \
  -e DB_NAME=your-database \
  -e DB_USER=your-user \
  -e DB_PASSWORD=your-password \
  mysql-mcp
```

## Cursor MCP Configuration

Add the following to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "mysql-database": {
      "url": "http://localhost:8001/sse",
      "env": {
        "DB_HOST": "your-mysql-host",
        "DB_PORT": "3306",
        "DB_NAME": "your-database",
        "DB_USER": "your-username",
        "DB_PASSWORD": "your-password"
      }
    }
  }
}
```

**Note**: When using Cursor MCP settings, the environment variables are provided by Cursor, so you don't need to set them in docker-compose. The server will read from the environment variables provided by Cursor.

## Available Tools

The server exposes 10 tools for database exploration:

### 1. `list_databases`
List all available databases in the MySQL server.

### 2. `list_tables`
List all tables and views in a specific database.

**Parameters:**
- `database` (string): Name of the database

**Returns:** List of tables/views with name, type, and comment

### 3. `describe_table`
Get detailed structure of a table including columns, types, and constraints.

**Parameters:**
- `database` (string): Name of the database
- `table` (string): Name of the table

**Returns:** Complete table structure with column details

### 4. `list_indexes`
List all indexes for a specific table.

**Parameters:**
- `database` (string): Name of the database
- `table` (string): Name of the table

**Returns:** List of index definitions

### 5. `list_foreign_keys`
List foreign key relationships for a table.

**Parameters:**
- `database` (string): Name of the database
- `table` (string): Name of the table

**Returns:** List of foreign key relationships

### 6. `get_view_definition`
Get the SQL definition of a view.

**Parameters:**
- `database` (string): Name of the database
- `view` (string): Name of the view

**Returns:** SQL definition string

### 7. `get_table_comments`
Get comments and metadata for all tables in a database.

**Parameters:**
- `database` (string): Name of the database

**Returns:** List of table metadata

### 8. `execute_query`
Execute a read-only SQL query safely.

**Parameters:**
- `query` (string): SQL SELECT query
- `limit` (int, optional): Maximum rows to return (default: 1000, max: 1000)

**Returns:** Query results with row count

**Safety:** Automatically blocks write operations (INSERT, UPDATE, DELETE, etc.)

### 9. `sample_data`
Sample rows from a table for inspection.

**Parameters:**
- `database` (string): Name of the database
- `table` (string): Name of the table
- `limit` (int, optional): Number of rows (default: 100, max: 1000)

**Returns:** Sample rows as dictionaries

### 10. `get_schema_metadata`
Get comprehensive metadata for an entire database schema.

**Parameters:**
- `database` (string): Name of the database

**Returns:** Complete schema summary with tables, views, and relationships

## Read-Only Guarantees

The server enforces read-only access through multiple mechanisms:

1. **SQL Keyword Filtering**: Blocks queries containing write keywords (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, etc.)
2. **Session-Level Read-Only**: Sets `SET SESSION TRANSACTION READ ONLY` on each connection
3. **Connection Isolation**: Each query uses a separate connection from the pool
4. **No Schema Mutations**: Only queries information_schema and user data, never modifies structure

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | MySQL server hostname | Required |
| `DB_PORT` | MySQL server port | `3306` |
| `DB_NAME` | Default database name | Optional |
| `DB_USER` | MySQL username | Required |
| `DB_PASSWORD` | MySQL password | Required |
| `DB_POOL_SIZE` | Connection pool size | `5` |
| `DB_READ_TIMEOUT` | Query timeout in seconds | `30` |
| `PORT` | Server port | `8001` |

## Development

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=password
export DB_NAME=testdb

# Run server
python -m mysql_mcp.server
```

### Project Structure

```
MysqlMcp/
├── src/
│   └── mysql_mcp/
│       ├── __init__.py
│       ├── server.py          # Fast MCP server entry point
│       ├── database.py         # MySQL connection & query utilities
│       └── tools.py            # MCP tool definitions
├── tests/                      # Test suite (to be added)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Safety Notes

- **Never** expose this server to the public internet without proper authentication
- Database credentials are provided via environment variables (never hardcoded)
- All queries are validated for read-only compliance
- Connection pooling prevents resource exhaustion
- Query timeouts prevent long-running operations

## Troubleshooting

### Connection Issues

If you see connection errors:

1. Verify MySQL is accessible from the container:
   ```bash
   docker-compose exec mysql-mcp ping your-mysql-host
   ```

2. Check environment variables:
   ```bash
   docker-compose exec mysql-mcp env | grep DB_
   ```

3. Test MySQL connection manually:
   ```bash
   docker-compose exec mysql-mcp python -c "import mysql.connector; print('OK')"
   ```

### Port Conflicts

If port 8001 is already in use, change it:

```bash
PORT=8002 docker-compose up -d
```

## License

MIT License - See LICENSE file for details
