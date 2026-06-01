#!/usr/bin/env python3
"""Quick test DB queries for dashboard"""
import sqlite3
import json
from datetime import date, timedelta

DB = "/home/priney/repos/personal-dashboard/data/dashboard.db"

def test():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    print("=== Трекеры ===")
    for row in conn.execute("SELECT * FROM trackers WHERE active = 1"):
        print(f"  {row['slug']}: {row['name']} ({row['type']})")

    print("\n=== Фокус-цели (active) ===")
    for row in conn.execute(
        "SELECT * FROM focus_goals WHERE status = 'active' ORDER BY priority DESC"
    ):
        print(f"  {row['slug']}: {row['title']} [{row['current_value']}/{row['target_value']} {row['metric_unit']}]")

    # Mark vitamins
    print("\n=== Отметить витамины ===")
    tracker = conn.execute("SELECT id FROM trackers WHERE slug = 'vitamins'").fetchone()
    if tracker:
        conn.execute(
            "INSERT OR REPLACE INTO tracker_entries (tracker_id, entry_date, value, notes) VALUES (?, ?, ?, ?)",
            (tracker['id'], date.today().isoformat(), 1, 'тест')
        )
        conn.commit()
        print("  ✅ Отмечено")

    # Show streak
    print("\n=== Streak витамины ===")
    rows = conn.execute(
        "SELECT entry_date, value FROM tracker_entries WHERE tracker_id = (SELECT id FROM trackers WHERE slug = 'vitamins') ORDER BY entry_date DESC"
    ).fetchall()
    streak = 0
    today = date.today()
    for r in rows:
        d = date.fromisoformat(r['entry_date'])
        delta = (today - d).days
        if delta == streak and r['value']:
            streak += 1
    print(f"  Текущий streak: {streak} {'дней подряд 🔥' if streak else '(только сегодня)'}  Всего записей: {len(rows)}")

    conn.close()

if __name__ == "__main__":
    test()
