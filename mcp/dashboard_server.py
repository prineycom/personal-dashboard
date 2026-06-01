#!/usr/bin/env python3
"""
Personal Dashboard MCP Server — официальный SDK (FastMCP).
Подключается к Hermes через stdio transport.

Нужно запускать: python3 mcp/dashboard_server.py
Или через venv:  .venv/bin/python mcp/dashboard_server.py
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import date

from mcp.server.fastmcp import FastMCP

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "dashboard.db"
SCHEMA_PATH = BASE_DIR / "schema" / "001_mvp.sql"

# Ensure DB exists with schema
def ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())
        conn.close()
    return str(DB_PATH)

DB_PATH_STR = ensure_db()

# Create MCP server
mcp = FastMCP("dashboard")

# Helper
def db():
    return sqlite3.connect(DB_PATH_STR)


@mcp.tool()
def list_trackers(active_only: bool = True) -> str:
    """Показать список активных трекеров."""
    conn = db()
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM trackers"
    if active_only:
        query += " WHERE active = 1"
    rows = conn.execute(query).fetchall()
    conn.close()
    return json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2)


@mcp.tool()
def mark_tracker(tracker_slug: str, value: float = 1.0, notes: str = "", entry_date: str | None = None) -> str:
    """Отметить выполнение трекера. tracker_slug — slug трекера."""
    entry_date = entry_date or date.today().isoformat()
    conn = db()
    conn.row_factory = sqlite3.Row
    tracker = conn.execute("SELECT id FROM trackers WHERE slug = ?", (tracker_slug,)).fetchone()
    if not tracker:
        conn.close()
        return json.dumps({"error": f"Трекер '{tracker_slug}' не найден"}, ensure_ascii=False)

    conn.execute(
        "INSERT OR REPLACE INTO tracker_entries (tracker_id, entry_date, value, notes) VALUES (?, ?, ?, ?)",
        (tracker["id"], entry_date, value, notes)
    )
    conn.commit()
    conn.close()
    return json.dumps({
        "success": True, "tracker": tracker_slug, "date": entry_date, "value": value
    }, ensure_ascii=False)


@mcp.tool()
def get_streak(tracker_slug: str) -> str:
    """Показать streak (дни подряд) для трекера."""
    conn = db()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT entry_date, value FROM tracker_entries
        WHERE tracker_id = (SELECT id FROM trackers WHERE slug = ?)
        ORDER BY entry_date DESC
    """, (tracker_slug,)).fetchall()
    conn.close()

    if not rows:
        return json.dumps({"streak": 0, "longest": 0, "total": 0}, ensure_ascii=False)

    streak = 0
    longest = 0
    today = date.today()
    for r in rows:
        d = date.fromisoformat(r["entry_date"])
        delta = (today - d).days
        if delta == streak and r["value"]:
            streak += 1

    return json.dumps({
        "streak": streak, "total_entries": len(rows), "tracker": tracker_slug
    }, ensure_ascii=False)


@mcp.tool()
def list_focus_goals(status: str = None) -> str:
    """Список фокус-целей. status: planned/active/completed/archived (опционально)."""
    conn = db()
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM focus_goals"
    params = ()
    if status:
        query += " WHERE status = ?"
        params = (status,)
    query += " ORDER BY priority DESC, deadline ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2)


@mcp.tool()
def add_focus_goal(slug: str, title: str, category: str, metric_unit: str, target_value: float,
                   deadline: str = None, priority: int = 3, status: str = "planned", context: str = "") -> str:
    """Создать новую фокус-цель. category: professional/health/finance/content/personal."""
    conn = db()
    try:
        conn.execute(
            """INSERT INTO focus_goals (slug, title, category, metric_unit, target_value, current_value, deadline, priority, status, context)
               VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)""",
            (slug, title, category, metric_unit, target_value, deadline, priority, status, context)
        )
        conn.commit()
        return json.dumps({"success": True, "slug": slug}, ensure_ascii=False)
    except sqlite3.IntegrityError:
        return json.dumps({"error": f"Цель '{slug}' уже существует"}, ensure_ascii=False)
    finally:
        conn.close()


@mcp.tool()
def update_goal_progress(slug: str, current_value: float) -> str:
    """Обновить прогресс фокус-цели."""
    conn = db()
    cur = conn.execute("UPDATE focus_goals SET current_value = ?, updated_at = CURRENT_TIMESTAMP WHERE slug = ?",
                       (current_value, slug))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return json.dumps({"error": f"Цель '{slug}' не найдена"}, ensure_ascii=False)
    return json.dumps({"success": True, "slug": slug, "current_value": current_value}, ensure_ascii=False)


# ── ЕЖЕДНЕВНИК ──────────────────────────────────────────────

@mcp.tool()
def get_daily_entry(entry_date: str | None = None) -> str:
    """Показать дневную запись (morning_review, evening_review, оценка дня). По умолчанию сегодня."""
    entry_date = entry_date or date.today().isoformat()
    conn = db()
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM daily_entries WHERE entry_date = ?", (entry_date,)).fetchone()
    conn.close()
    if not row:
        return json.dumps({"entry_date": entry_date, "exists": False}, ensure_ascii=False)
    return json.dumps(dict(row), ensure_ascii=False, indent=2)


@mcp.tool()
def save_daily_entry(entry_date: str | None = None,
                     morning_review: str = "",
                     evening_review: str = "",
                     day_score: int = 0,
                     energy_morning: int = 0,
                     todo_list: str = "") -> str:
    """Сохранить дневную запись. entry_date = YYYY-MM-DD (по умолчанию сегодня). todo_list = JSON array строк."""
    entry_date = entry_date or date.today().isoformat()
    conn = db()
    try:
        conn.execute("""
            INSERT INTO daily_entries (entry_date, morning_review, evening_review, day_score, energy_morning, todo_list)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(entry_date) DO UPDATE SET
                morning_review = excluded.morning_review,
                evening_review = excluded.evening_review,
                day_score = excluded.day_score,
                energy_morning = excluded.energy_morning,
                todo_list = excluded.todo_list,
                updated_at = CURRENT_TIMESTAMP
        """, (entry_date, morning_review, evening_review, day_score, energy_morning, todo_list))
        conn.commit()
        return json.dumps({"success": True, "entry_date": entry_date}, ensure_ascii=False)
    finally:
        conn.close()


# ── ЗДОРОВЬЕ ──────────────────────────────────────────────

@mcp.tool()
def get_health_log(entry_date: str | None = None) -> str:
    """Показать запись здоровья за день (вес, сон, шаги, пульс). По умолчанию сегодня."""
    entry_date = entry_date or date.today().isoformat()
    conn = db()
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM health_daily WHERE entry_date = ?", (entry_date,)).fetchone()
    conn.close()
    if not row:
        return json.dumps({"entry_date": entry_date, "exists": False}, ensure_ascii=False)
    return json.dumps(dict(row), ensure_ascii=False, indent=2)


@mcp.tool()
def save_health_log(entry_date: str | None = None,
                    weight: float = 0,
                    sleep_hours: float = 0,
                    steps: int = 0,
                    heart_avg: int = 0) -> str:
    """Сохранить запись здоровья. entry_date = YYYY-MM-DD (по умолчанию сегодня)."""
    entry_date = entry_date or date.today().isoformat()
    conn = db()
    try:
        conn.execute("""
            INSERT INTO health_daily (entry_date, weight, sleep_hours, steps, heart_avg)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(entry_date) DO UPDATE SET
                weight = excluded.weight,
                sleep_hours = excluded.sleep_hours,
                steps = excluded.steps,
                heart_avg = excluded.heart_avg
        """, (entry_date, weight, sleep_hours, steps, heart_avg))
        conn.commit()
        return json.dumps({"success": True, "entry_date": entry_date}, ensure_ascii=False)
    finally:
        conn.close()


if __name__ == "__main__":
    mcp.run()
