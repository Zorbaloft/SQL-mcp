.PHONY: help install install-dev test test-verbose run run-server docker-build docker-up docker-down docker-logs docker-restart clean lint format check

# Default target
help:
	@echo "MySQL MCP Server - Available Commands:"
	@echo ""
	@echo "  make install          - Install production dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make test            - Run tests"
	@echo "  make test-verbose    - Run tests with verbose output"
	@echo "  make run             - Run the server locally"
	@echo "  make run-server      - Run the server (alias for run)"
	@echo "  make docker-build    - Build Docker image"
	@echo "  make docker-up       - Start Docker container"
	@echo "  make docker-down     - Stop Docker container"
	@echo "  make docker-logs     - View Docker logs"
	@echo "  make docker-restart  - Restart Docker container"
	@echo "  make clean           - Clean Python cache and build files"
	@echo "  make check           - Run all checks (tests, lint, etc.)"
	@echo ""

# Install production dependencies
install:
	pip install -r requirements.txt

# Install development dependencies (same as production for now)
install-dev:
	pip install -r requirements.txt

# Run tests
test:
	pytest

# Run tests with verbose output
test-verbose:
	pytest -v -s

# Run the server locally
run run-server:
	PYTHONPATH=src python -m mysql_mcp.server

# Docker commands
docker-build:
	docker build -t mysql-mcp .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f mysql-mcp

docker-restart:
	docker-compose restart mysql-mcp

# Clean Python cache and build files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true

# Run all checks
check: test
