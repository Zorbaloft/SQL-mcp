"""MySQL database connection and query utilities with read-only enforcement."""

import os
import re
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error, pooling


class ReadOnlyError(Exception):
    """Raised when a write operation is attempted."""

    pass


class DatabaseManager:
    """Manages MySQL connections with read-only enforcement."""

    # SQL keywords that indicate write operations
    WRITE_KEYWORDS = [
        r'\bINSERT\b',
        r'\bUPDATE\b',
        r'\bDELETE\b',
        r'\bDROP\b',
        r'\bALTER\b',
        r'\bCREATE\b',
        r'\bTRUNCATE\b',
        r'\bREPLACE\b',
        r'\bGRANT\b',
        r'\bREVOKE\b',
        r'\bLOCK\b',
        r'\bUNLOCK\b',
    ]

    def __init__(self):
        """Initialize database manager with connection pool."""
        self.pool: Optional[pooling.MySQLConnectionPool] = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize MySQL connection pool from environment variables."""
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'database': os.getenv('DB_NAME', ''),
            'user': os.getenv('DB_USER', ''),
            'password': os.getenv('DB_PASSWORD', ''),
            'pool_name': 'mysql_mcp_pool',
            'pool_size': int(os.getenv('DB_POOL_SIZE', '5')),
            'pool_reset_session': True,
            'autocommit': False,
            'read_timeout': int(os.getenv('DB_READ_TIMEOUT', '30')),
            'raise_on_warnings': False,
        }

        try:
            self.pool = pooling.MySQLConnectionPool(**config)
        except Error as e:
            raise RuntimeError(f"Failed to initialize database pool: {e}") from e

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        conn = None
        try:
            conn = self.pool.get_connection()
            # Ensure read-only mode
            cursor = conn.cursor()
            cursor.execute("SET SESSION TRANSACTION READ ONLY")
            cursor.close()
            yield conn
        finally:
            if conn and conn.is_connected():
                conn.close()

    def _is_read_only_query(self, query: str) -> bool:
        """Check if query contains write operations."""
        query_upper = query.upper().strip()
        for pattern in self.WRITE_KEYWORDS:
            if re.search(pattern, query_upper):
                return False
        return True

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Execute a read-only query and return results.

        Args:
            query: SQL query string
            params: Optional parameters for parameterized query
            fetch_one: If True, return only first row
            fetch_all: If True, return all rows

        Returns:
            List of dictionaries representing rows

        Raises:
            ReadOnlyError: If query contains write operations
        """
        if not self._is_read_only_query(query):
            raise ReadOnlyError(
                "Write operations are not allowed. This server is read-only."
            )

        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if fetch_one:
                    result = cursor.fetchone()
                    return [result] if result else []
                elif fetch_all:
                    return cursor.fetchall()
                else:
                    return []
            except Error as e:
                raise RuntimeError(f"Query execution failed: {e}") from e
            finally:
                cursor.close()

    def list_databases(self) -> List[str]:
        """List all available databases."""
        query = "SHOW DATABASES"
        results = self.execute_query(query)
        return [row['Database'] for row in results]

    def list_tables(self, database: str) -> List[Dict[str, str]]:
        """List tables and views in a database."""
        query = """
            SELECT 
                TABLE_NAME as name,
                TABLE_TYPE as type,
                TABLE_COMMENT as comment
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_TYPE, TABLE_NAME
        """
        results = self.execute_query(query, (database,))
        return results

    def describe_table(self, database: str, table: str) -> Dict[str, Any]:
        """Get detailed table structure."""
        # Get columns
        columns_query = """
            SELECT 
                COLUMN_NAME as name,
                COLUMN_TYPE as type,
                IS_NULLABLE as nullable,
                COLUMN_DEFAULT as default_value,
                COLUMN_KEY as key_type,
                EXTRA as extra,
                COLUMN_COMMENT as comment
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        columns = self.execute_query(columns_query, (database, table))

        # Get table comment
        table_query = """
            SELECT TABLE_COMMENT as comment
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """
        table_info = self.execute_query(table_query, (database, table))
        table_comment = table_info[0]['comment'] if table_info else None

        return {
            'database': database,
            'table': table,
            'comment': table_comment,
            'columns': columns,
        }

    def list_indexes(self, database: str, table: str) -> List[Dict[str, Any]]:
        """List indexes for a table."""
        query = """
            SELECT 
                INDEX_NAME as name,
                COLUMN_NAME as column_name,
                SEQ_IN_INDEX as sequence,
                NON_UNIQUE as non_unique,
                INDEX_TYPE as type,
                INDEX_COMMENT as comment
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """
        return self.execute_query(query, (database, table))

    def list_foreign_keys(self, database: str, table: str) -> List[Dict[str, Any]]:
        """List foreign key relationships for a table."""
        query = """
            SELECT 
                CONSTRAINT_NAME as constraint_name,
                COLUMN_NAME as column_name,
                REFERENCED_TABLE_SCHEMA as referenced_database,
                REFERENCED_TABLE_NAME as referenced_table,
                REFERENCED_COLUMN_NAME as referenced_column,
                UPDATE_RULE as update_rule,
                DELETE_RULE as delete_rule
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = %s
                AND REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY CONSTRAINT_NAME, ORDINAL_POSITION
        """
        return self.execute_query(query, (database, table))

    def get_view_definition(self, database: str, view: str) -> Optional[str]:
        """Get SQL definition of a view."""
        query = """
            SELECT VIEW_DEFINITION as definition
            FROM information_schema.VIEWS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """
        results = self.execute_query(query, (database, view))
        return results[0]['definition'] if results else None

    def sample_data(
        self, database: str, table: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Sample rows from a table."""
        if limit > 1000:
            limit = 1000  # Hard cap

        # Use parameterized query with proper escaping
        # Note: MySQL connector handles identifier escaping via backticks in format string
        # but we validate database/table names are alphanumeric/underscore to prevent injection
        if not re.match(r'^[a-zA-Z0-9_]+$', database) or not re.match(r'^[a-zA-Z0-9_]+$', table):
            raise ValueError("Invalid database or table name")

        query = f"SELECT * FROM `{database}`.`{table}` LIMIT %s"
        return self.execute_query(query, (limit,))


# Global instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
