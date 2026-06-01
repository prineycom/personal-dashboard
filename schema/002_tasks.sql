-- tasks.sql : бэклог задач (self-hosted до TickTick интеграции)

CREATE TABLE IF NOT EXISTS task_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#4A90D9',
    icon TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN ('inbox', 'active', 'completed', 'archived')) DEFAULT 'inbox',
    priority INTEGER CHECK(priority BETWEEN 1 AND 4) DEFAULT 3,
    project_id INTEGER,
    focus_goal_id INTEGER,
    due_date DATE,
    scheduled_date DATE,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES task_projects(id),
    FOREIGN KEY (focus_goal_id) REFERENCES focus_goals(id)
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due ON tasks(due_date);
CREATE INDEX idx_tasks_goal ON tasks(focus_goal_id);
