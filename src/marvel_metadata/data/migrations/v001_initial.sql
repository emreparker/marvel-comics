-- Marvel Metadata Schema v1
-- Initial schema with normalized tables for issues, series, creators, and covers

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now')),
    description TEXT
);

-- Series table (normalized)
CREATE TABLE IF NOT EXISTS series (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Main issues table
CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY,
    digital_id INTEGER,
    title TEXT NOT NULL,
    issue_number TEXT,
    description TEXT,
    modified TEXT,
    page_count INTEGER,
    detail_url TEXT NOT NULL,

    -- Foreign key to series
    series_id INTEGER,

    -- Dates
    on_sale_date TEXT,
    unlimited_date TEXT,

    -- Source tracking
    year_page INTEGER,

    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (series_id) REFERENCES series(id)
);

-- Creators table
CREATE TABLE IF NOT EXISTS creators (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Junction table for issue<->creator relationships
CREATE TABLE IF NOT EXISTS issue_creators (
    issue_id INTEGER NOT NULL,
    creator_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY (issue_id, creator_id, role),
    FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
    FOREIGN KEY (creator_id) REFERENCES creators(id) ON DELETE CASCADE
);

-- Cover images table
CREATE TABLE IF NOT EXISTS covers (
    issue_id INTEGER PRIMARY KEY,
    path TEXT NOT NULL,
    extension TEXT,
    FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
);

-- Indexes for common queries

-- Issues indexes
CREATE INDEX IF NOT EXISTS idx_issues_title ON issues(title);
CREATE INDEX IF NOT EXISTS idx_issues_series_id ON issues(series_id);
CREATE INDEX IF NOT EXISTS idx_issues_year_page ON issues(year_page);
CREATE INDEX IF NOT EXISTS idx_issues_on_sale_date ON issues(on_sale_date);
CREATE INDEX IF NOT EXISTS idx_issues_unlimited_date ON issues(unlimited_date);
CREATE INDEX IF NOT EXISTS idx_issues_digital_id ON issues(digital_id);

-- Issue creators indexes
CREATE INDEX IF NOT EXISTS idx_issue_creators_issue ON issue_creators(issue_id);
CREATE INDEX IF NOT EXISTS idx_issue_creators_creator ON issue_creators(creator_id);
CREATE INDEX IF NOT EXISTS idx_issue_creators_role ON issue_creators(role);

-- Creators index
CREATE INDEX IF NOT EXISTS idx_creators_name ON creators(name);

-- Series index
CREATE INDEX IF NOT EXISTS idx_series_name ON series(name);

-- Record the schema version
INSERT OR REPLACE INTO schema_version (version, description)
VALUES (1, 'Initial schema with issues, series, creators, covers');
