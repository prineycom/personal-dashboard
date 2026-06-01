#!/bin/bash
# Wrapper для запуска Dashboard MCP сервера с правильным venv
BASE="/home/priney/repos/personal-dashboard"
source "$BASE/.venv/bin/activate"
exec "$BASE/.venv/bin/python" "$BASE/mcp/dashboard_server.py"
