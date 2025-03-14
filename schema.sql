
-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    source_file TEXT,
    source_path TEXT,
    created_at TEXT
);

-- Elements table
CREATE TABLE IF NOT EXISTS elements (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    element_data TEXT,
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects (id)
);

-- POMs table
CREATE TABLE IF NOT EXISTS poms (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    file_path TEXT,
    pom_data TEXT,
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects (id)
);

-- Test cases table
CREATE TABLE IF NOT EXISTS test_cases (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    pom_id TEXT NOT NULL,
    name TEXT,
    script_path TEXT,
    description TEXT,
    created_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects (id),
    FOREIGN KEY (pom_id) REFERENCES poms (id)
);

-- Test executions table
CREATE TABLE IF NOT EXISTS test_executions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    test_id TEXT NOT NULL,
    status TEXT,
    result_data TEXT,
    log_path TEXT,
    executed_at TEXT,
    FOREIGN KEY (project_id) REFERENCES projects (id),
    FOREIGN KEY (test_id) REFERENCES test_cases (id)
);
