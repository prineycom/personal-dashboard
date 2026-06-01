#!/usr/bin/env python3
"""
MCP Server for Personal Dashboard.
Унифицированный доступ к БД dashboard (SQLite для MVP, PostgreSQL/Supabase в production).

Supports: focus_goals, trackers, tracker_entries, daily_entries, health_daily
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, date

# MCP Protocol
# stdio mode: reads JSON-RPC on stdin, writes to stdout

DB_PATH = os.getenv("DASHBOARD_DB", str(Path(__file__).resolve().parent.parent / "data" / "dashboard.db"))


def ensure_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    with open(Path(__file__).resolve().parent.parent / "schema" / "001_mvp.sql", "r") as f:
        conn.executescript(f.read())
    conn.close()


class DashboardDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def list_trackers(self, active_only: bool = True):
        query = "SELECT * FROM trackers"
        if active_only:
            query += " WHERE active = 1"
        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def mark_tracker(self, tracker_slug: str, value: float = 1.0, notes: str = "", entry_date: str | None = None):
        entry_date = entry_date or date.today().isoformat()
        tracker = self.conn.execute("SELECT id FROM trackers WHERE slug = ?", (tracker_slug,)).fetchone()
        if not tracker:
            return {"error": f"Трекер '{tracker_slug}' не найден"}

        try:
            self.conn.execute(
                """INSERT OR REPLACE INTO tracker_entries (tracker_id, entry_date, value, notes)
                   VALUES (?, ?, ?, ?)""",
                (tracker["id"], entry_date, value, notes)
            )
            self.conn.commit()
            return {"success": True, "tracker": tracker_slug, "date": entry_date, "value": value}
        except Exception as e:
            return {"error": str(e)}

    def get_streak(self, tracker_slug: str):
        cursor = self.conn.execute("""
            SELECT entry_date, value FROM tracker_entries
            WHERE tracker_id = (SELECT id FROM trackers WHERE slug = ?)
            ORDER BY entry_date DESC
        """, (tracker_slug,))
        rows = cursor.fetchall()
        if not rows:
            return {"streak": 0, "longest": 0}

        streak = 0
        today = date.today()
        for row in rows:
            row_date = datetime.strptime(row["entry_date"], "%Y-%m-%d").date()
            delta = (today - row_date).days
            if delta == streak and row["value"]:
                streak += 1
            elif delta > streak:
                break

        return {"streak": streak, "total_entries": len(rows)}

    def list_focus_goals(self, status: str = None):
        query = "SELECT * FROM focus_goals"
        params = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY priority DESC, deadline ASC"
        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()


# MCP Tool Definitions
TOOLS = {
    "list_trackers": {
        "description": "Показать список активных трекеров",
        "parameters": {
            "type": "object",
            "properties": {
                "active_only": {"type": "boolean", "default": True}
            }
        }
    },
    "mark_tracker": {
        "description": "Отметить выполнение трекера. tracker_slug — slug трекера",
        "parameters": {
            "type": "object",
            "properties": {
                "tracker_slug": {"type": "string"},
                "value": {"type": "number", "default": 1},
                "notes": {"type": "string", "default": ""},
                "entry_date": {"type": "string", "description": "YYYY-MM-DD, по умолчанию сегодня"}
            },
            "required": ["tracker_slug"]
        }
    },
    "get_streak": {
        "description": "Показать streak (дни подряд) для трекера",
        "parameters": {
            "type": "object",
            "properties": {
                "tracker_slug": {"type": "string"}
            },
            "required": ["tracker_slug"]
        }
    },
    "list_focus_goals": {
        "description": "Список фокус-целей. status: planned/active/completed/archived",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["planned", "active", "completed", "archived"]}
            }
        }
    }
}


def handle_request(request: dict) -> dict:
    method = request.get("method", "")
    params = request.get("params", {})

    if method == "initialize":
        return {"tools": TOOLS}

    db = DashboardDB()
    try:
        if method == "tools/list":
            return {"tools": [{"name": k, **v} for k, v in TOOLS.items()]}

        elif method == "tools/call":
            tool = params.get("name", "")
            args = params.get("arguments", {})

            if tool == "list_trackers":
                return {"content": db.list_trackers(args.get("active_only", True))}
            elif tool == "mark_tracker":
                return {"content": db.mark_tracker(
                    args["tracker_slug"],
                    args.get("value", 1.0),
                    args.get("notes", ""),
                    args.get("entry_date")
                )}
            elif tool == "get_streak":
                return {"content": db.get_streak(args["tracker_slug"])}
            elif tool == "list_focus_goals":
                return {"content": db.list_focus_goals(args.get("status"))}
            else:
                return {"error": f"Неизвестный тул: {tool}"}

        return {"error": "Неизвестный метод"}
    finally:
        db.close()


def main():
    ensure_db()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response, default=str))
            sys.stdout.flush()
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON"}))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
