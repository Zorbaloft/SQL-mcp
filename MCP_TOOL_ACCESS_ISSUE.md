# MCP Tool Access Issue - Diagnostic

## Problem
The mysql-database MCP server is running, but the tools (`list_databases`, `list_tables`, etc.) are not accessible from Cursor's AI assistant.

## Root Cause Analysis

### Tools Are Properly Defined
- ✅ All 10 tools are correctly defined in `src/mysql_mcp/tools.py`
- ✅ Tools use `@mcp.tool()` decorator from FastMCP
- ✅ Server runs with SSE transport on port 8001

### Expected Tool Naming Pattern
Based on other MCP servers (like `mcp-atlassian`), tools should be prefixed with:
- Pattern: `mcp_{server-name}_{tool-name}`
- Expected: `mcp_mysql-database_list_databases`, `mcp_mysql-database_list_tables`, etc.

### Potential Issues

1. **Cursor MCP Server Registration**
   - Cursor may not have successfully connected to the MCP server
   - The server name in config (`mysql-database`) might not match FastMCP's server name (`MySQL MCP Server`)

2. **FastMCP Server Name Mismatch**
   - FastMCP instance is created with: `FastMCP("MySQL MCP Server")`
   - Cursor config uses: `"mysql-database"`
   - These names don't match, which might cause registration issues

3. **SSE Endpoint Configuration**
   - URL is: `http://localhost:8001/sse`
   - Need to verify this endpoint is actually serving the MCP protocol

## Recommended Fixes

### Fix 1: Align Server Names
Update `src/mysql_mcp/tools.py` to match the Cursor config:

```python
# Change from:
mcp = FastMCP("MySQL MCP Server")

# To:
mcp = FastMCP("mysql-database")
```

### Fix 2: Verify Cursor MCP Connection
1. Open Cursor Settings → Features → Model Context Protocol
2. Check if `mysql-database` appears in the list of connected servers
3. Look for any error messages or connection status indicators
4. Restart Cursor after making config changes

### Fix 3: Test SSE Endpoint Directly
Test if the SSE endpoint is responding:

```bash
curl -v http://localhost:8001/sse
```

Should return SSE stream or MCP protocol messages.

### Fix 4: Check Server Logs
Check if the server is receiving connection attempts:

```bash
docker-compose logs mysql-mcp
# or
docker logs mysql-mcp-server
```

## Verification Steps

After applying fixes:

1. **Restart Cursor completely** (not just reload window)
2. **Check MCP server status** in Cursor settings
3. **Try accessing tools** - they should appear as:
   - `mcp_mysql-database_list_databases`
   - `mcp_mysql-database_list_tables`
   - etc.

## Alternative: Direct Tool Access Test

If tools still don't appear, we can test the server directly by:
1. Making a direct HTTP request to the MCP server
2. Checking the `/sse` endpoint response
3. Verifying tool registration via MCP protocol
