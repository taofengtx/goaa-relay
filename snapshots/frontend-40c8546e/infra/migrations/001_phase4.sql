-- GOAA Phase 4 Schema Migration
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS projects (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL UNIQUE,
    description TEXT, created_by VARCHAR(100),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    archived    BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS models (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider        VARCHAR(50) NOT NULL,
    model_name      VARCHAR(100) NOT NULL,
    display_name    VARCHAR(100),
    endpoint_url    TEXT NOT NULL,
    api_key_encrypted BYTEA,
    capabilities    JSONB DEFAULT '{}',
    max_tokens      INT DEFAULT 4096,
    is_active       BOOLEAN DEFAULT TRUE,
    is_default      BOOLEAN DEFAULT FALSE,
    cost_per_1k_in  NUMERIC(10,6),
    cost_per_1k_out NUMERIC(10,6),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    description     TEXT, persona TEXT,
    model_id        UUID REFERENCES models(id),
    preferred_nodes JSONB DEFAULT '[]',
    max_concurrent  INT DEFAULT 5,
    requires_docker BOOLEAN DEFAULT FALSE,
    requires_ollama BOOLEAN DEFAULT FALSE,
    requires_gpu    BOOLEAN DEFAULT FALSE,
    learning_status VARCHAR(20) DEFAULT 'pending',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, name)
);

CREATE TABLE IF NOT EXISTS agent_documents (
    agent_id    UUID REFERENCES agents(id) ON DELETE CASCADE,
    doc_path    TEXT NOT NULL,
    doc_md5     VARCHAR(32),
    learned_at  TIMESTAMPTZ,
    summary     TEXT,
    chunk_count INT DEFAULT 0,
    PRIMARY KEY (agent_id, doc_path)
);

CREATE TABLE IF NOT EXISTS agent_memory (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id       UUID REFERENCES agents(id) ON DELETE CASCADE,
    source_doc     TEXT,
    chunk_text     TEXT NOT NULL,
    embedding_data BYTEA,
    metadata       JSONB DEFAULT '{}',
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS nodes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_id       VARCHAR(50) UNIQUE NOT NULL,
    display_name    VARCHAR(100),
    node_type       VARCHAR(20),
    ip_address      INET NOT NULL,
    ssh_user        VARCHAR(50) DEFAULT 'root',
    ssh_port        INT DEFAULT 22,
    ssh_key_encrypted BYTEA,
    auth_type       VARCHAR(20),
    os_info         JSONB DEFAULT '{}',
    tags            JSONB DEFAULT '[]',
    is_active       BOOLEAN DEFAULT TRUE,
    last_deployment_at TIMESTAMPTZ,
    last_audit_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    title           VARCHAR(200),
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ DEFAULT NOW(),
    archived        BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS messages (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id  UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role        VARCHAR(20),
    agent_id    UUID REFERENCES agents(id),
    content     TEXT NOT NULL,
    model_used  VARCHAR(100),
    tokens_in   INT DEFAULT 0,
    tokens_out  INT DEFAULT 0,
    cost_usd    NUMERIC(10,6) DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    id          VARCHAR(50) PRIMARY KEY,
    project_id  UUID REFERENCES projects(id),
    task_type   VARCHAR(50) NOT NULL,
    worker_id   VARCHAR(50),
    model_used  VARCHAR(100),
    priority    INT DEFAULT 5,
    status      VARCHAR(20) DEFAULT 'pending',
    payload     JSONB DEFAULT '{}',
    result      JSONB DEFAULT '{}',
    revenue_usd NUMERIC(10,6) DEFAULT 0,
    cost_usd    NUMERIC(10,6) DEFAULT 0,
    duration_ms INT DEFAULT 0,
    error_msg   TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    started_at  TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_tasks_status      ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_worker_id   ON tasks(worker_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at  ON tasks(created_at DESC);

CREATE TABLE IF NOT EXISTS audit_log (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp   TIMESTAMPTZ DEFAULT NOW(),
    action      VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id   UUID,
    operator    VARCHAR(100),
    details     JSONB DEFAULT '{}',
    ip_address  INET
);

INSERT INTO projects (name, description, created_by)
VALUES ('GOAA.AI v3.0', 'Default project for GOAA platform', 'system')
ON CONFLICT (name) DO NOTHING;

SELECT 'Phase 4 migration completed' AS status;
