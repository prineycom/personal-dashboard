-- Personal Dashboard: MVP схема SQLite (мигрируется на Supabase PostgreSQL)

-- Фокус-цели (центральный компас системы)
CREATE TABLE IF NOT EXISTS focus_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL, -- machine-readable ID
    title TEXT NOT NULL,
    category TEXT CHECK(category IN ('professional', 'health', 'finance', 'content', 'personal')),
    metric_unit TEXT,
    target_value REAL,
    current_value REAL DEFAULT 0,
    deadline DATE,
    priority INTEGER CHECK(priority BETWEEN 1 AND 5) DEFAULT 3,
    status TEXT CHECK(status IN ('planned', 'active', 'completed', 'archived')) DEFAULT 'planned',
    project_link TEXT, -- wikilink style
    context TEXT, -- markdown notes
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Трекеры (привычки, метрики)
CREATE TABLE IF NOT EXISTS trackers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('boolean', 'metric')) DEFAULT 'boolean',
    unit TEXT, -- для metric: 'мин', 'раз', 'гр'
    icon TEXT, -- emoji
    focus_goal_id INTEGER,
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (focus_goal_id) REFERENCES focus_goals(id)
);

-- Ежедневные записи трекеров
CREATE TABLE IF NOT EXISTS tracker_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracker_id INTEGER NOT NULL,
    entry_date DATE NOT NULL,
    value REAL, -- 1/0 для boolean, число для metric
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tracker_id) REFERENCES trackers(id),
    UNIQUE (tracker_id, entry_date)
);

-- Дневное логирование (ежедневник)
CREATE TABLE IF NOT EXISTS daily_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date DATE UNIQUE NOT NULL,
    morning_review TEXT,
    evening_review TEXT,
    day_score INTEGER CHECK(day_score BETWEEN 1 AND 5),
    energy_morning INTEGER CHECK(energy_morning BETWEEN 1 AND 5),
    todo_list TEXT, -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Health логи
CREATE TABLE IF NOT EXISTS health_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date DATE UNIQUE NOT NULL,
    weight REAL,
    sleep_hours REAL,
    steps INTEGER,
    heart_avg INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Индексы
CREATE INDEX idx_focus_goals_status ON focus_goals(status);
CREATE INDEX idx_focus_goals_priority ON focus_goals(priority);
CREATE INDEX idx_tracker_entries_date ON tracker_entries(entry_date);
CREATE INDEX idx_tracker_entries_tracker ON tracker_entries(tracker_id);
