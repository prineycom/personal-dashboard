#!/usr/bin/env python3
"""
Инициализация тестовых данных для Personal Dashboard
"""

import os
import sqlite3
from pathlib import Path

DB_PATH = os.getenv("DASHBOARD_DB", str(Path(__file__).resolve().parent.parent / "data" / "dashboard.db"))
SCHEMA_PATH = str(Path(__file__).resolve().parent.parent / "schema" / "001_mvp.sql")

def init_data():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    # Сначала схема
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())

    # Фокус-цели (примеры)
    focus_goals = [
        ("articles-q2-2026", "10 статей про AI", "content", "статей", 10, 3, "2026-08-01", 5, "active"),
        ("crypto-invest-2026", "Инвестиции 3000 USDT", "finance", "USDT", 3000, 1200, "2026-12-31", 5, "active"),
        ("running-form", "Беговая форма", "health", "раз/неделю", 3, 2, None, 4, "active"),
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO focus_goals (slug, title, category, metric_unit, target_value, current_value, deadline, priority, status) VALUES (?,?,?,?,?,?,?,?,?)",
        focus_goals
    )

    # Трекеры (примеры)
    trackers = [
        ("vitamins", "Витамины (D3, Mg, Омега)", "boolean", None, "💊", 2, 1),  # Привязано к health goal (id=3)
        ("coworking", "Посещение коворкинга", "boolean", None, "💻", None, 1),
        ("reading", "Чтение книги", "metric", "мин", "📚", 1, 1),  # Привязано к content goal (id=1)
        ("running", "Бег", "boolean", None, "🏃", 3, 1),  # Привязано к health goal (id=3)
        ("meditation", "Медитация", "boolean", None, "🧘", None, 1),
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO trackers (slug, name, type, unit, icon, focus_goal_id, active) VALUES (?,?,?,?,?,?,?)",
        trackers
    )

    conn.commit()
    conn.close()
    print(f"✅ Данные инициализированы в {DB_PATH}")

if __name__ == "__main__":
    init_data()
