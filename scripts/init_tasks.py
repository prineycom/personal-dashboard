#!/usr/bin/env python3
"""Инициализация тестовых задач и проектов."""

import sqlite3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp.dashboard_server import DB_PATH_STR

def init():
    conn = sqlite3.connect(DB_PATH_STR)
    conn.row_factory = sqlite3.Row

    # Проекты
    projects = [
        ('dashboard', 'Personal Dashboard', '#4A90D9', '📊', 'Система управления жизнью'),
        ('voca', 'Voca AI', '#7B68EE', '🎙️', 'Голосовой ассистент'),
        ('content', 'Контент', '#FF6B6B', '✍️', 'Статьи, курсы, книга'),
        ('life', 'Личное', '#51CF66', '🏠', 'Здоровье, быт, отношения'),
    ]
    for slug, name, color, icon, desc in projects:
        conn.execute(
            "INSERT OR IGNORE INTO task_projects (slug, name, color, icon, description) VALUES (?, ?, ?, ?, ?)",
            (slug, name, color, icon, desc)
        )
    conn.commit()

    project_map = {r['slug']: r['id'] for r in conn.execute("SELECT id, slug FROM task_projects").fetchall()}
    focus_map = {r['slug']: r['id'] for r in conn.execute("SELECT id, slug FROM focus_goals").fetchall()}

    tasks = [
        ('Добавить задачи в MCP сервер', 'Бэклог задач через MCP tools', 'active', 1, 'dashboard', 'build_system', '2026-06-05'),
        ('Исследовать TickTick API', 'Проверить официальное API и интеграцию', 'inbox', 2, 'dashboard', '', None),
        ('Записать демо VoxCPM', 'Тест TTS с реальным диалогом', 'active', 1, 'voca', '', '2026-06-10'),
        ('Написать главу 1 книги', 'Введение + обзор рынка', 'active', 2, 'content', 'write_book', '2026-06-15'),
        ('Пробежка 5км', 'Вечерний бег в парке', 'inbox', 1, 'life', 'run_marathon', '2026-06-02'),
        ('Прочитать 30 минут', 'LP的准备', 'inbox', 2, 'content', 'run_marathon', None),
    ]

    for title, desc, status, priority, proj_slug, goal_slug, due in tasks:
        proj_id = project_map.get(proj_slug)
        goal_id = focus_map.get(goal_slug) if goal_slug else None
        conn.execute(
            """INSERT INTO tasks (title, description, status, priority, project_id, focus_goal_id, due_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, desc, status, priority, proj_id, goal_id, due)
        )
    conn.commit()

    print("=== Задачи инициализированы ===")
    for status in ['inbox', 'active', 'completed']:
        count = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = ?", (status,)).fetchone()[0]
        print(f"  {status}: {count}")
    print(f"  Всего: {conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]}")
    conn.close()

if __name__ == "__main__":
    init()
