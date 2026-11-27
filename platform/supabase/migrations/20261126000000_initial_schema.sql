-- Generated from backend/alembic (revision 0001) with `alembic upgrade head --sql`.
-- Prefer running Alembic against Supabase directly (DATABASE_URL); this file is for the Supabase SQL editor / CLI.
-- RLS: the browser never talks to these tables directly (all access goes through the FastAPI backend
-- with the service connection), so RLS is enabled with no policies, which denies PostgREST access.

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE jobs (
    id VARCHAR(36) NOT NULL, 
    job_type VARCHAR(48) NOT NULL, 
    payload JSONB NOT NULL, 
    status VARCHAR(16) NOT NULL, 
    attempts INTEGER NOT NULL, 
    max_attempts INTEGER NOT NULL, 
    progress JSONB NOT NULL, 
    result JSONB, 
    error TEXT, 
    locked_by VARCHAR(128), 
    heartbeat_at TIMESTAMP WITH TIME ZONE, 
    run_after TIMESTAMP WITH TIME ZONE NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE, 
    finished_at TIMESTAMP WITH TIME ZONE, 
    subject_type VARCHAR(32), 
    subject_id VARCHAR(36), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_jobs_status_run_after ON jobs (status, run_after);

CREATE INDEX ix_jobs_subject_id ON jobs (subject_id);

CREATE TABLE llm_usage (
    id SERIAL NOT NULL, 
    provider VARCHAR(32) NOT NULL, 
    model VARCHAR(64) NOT NULL, 
    purpose VARCHAR(64) NOT NULL, 
    input_tokens INTEGER NOT NULL, 
    output_tokens INTEGER NOT NULL, 
    cache_read_tokens INTEGER NOT NULL, 
    cost_usd FLOAT NOT NULL, 
    job_id VARCHAR(36), 
    subject_id VARCHAR(36), 
    success BOOLEAN NOT NULL, 
    error TEXT, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE papers (
    id VARCHAR(36) NOT NULL, 
    title TEXT NOT NULL, 
    normalized_title TEXT NOT NULL, 
    authors JSONB NOT NULL, 
    doi VARCHAR(255), 
    arxiv_id VARCHAR(64), 
    openalex_id VARCHAR(64), 
    semantic_scholar_id VARCHAR(64), 
    abstract TEXT, 
    published_date DATE, 
    venue TEXT, 
    categories JSONB NOT NULL, 
    landing_url TEXT, 
    pdf_url TEXT, 
    pdf_path TEXT, 
    pdf_sha256 VARCHAR(64), 
    is_open_access BOOLEAN, 
    license TEXT, 
    "references" JSONB NOT NULL, 
    cited_by_count INTEGER, 
    discovered_via VARCHAR(32) NOT NULL, 
    status VARCHAR(32) NOT NULL, 
    processing_error TEXT, 
    text_extractor VARCHAR(64), 
    page_count INTEGER, 
    latex_source TEXT, 
    latex_files JSONB NOT NULL, 
    source_metadata JSONB NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (arxiv_id), 
    UNIQUE (doi), 
    UNIQUE (openalex_id), 
    UNIQUE (semantic_scholar_id)
);

CREATE INDEX ix_papers_normalized_title ON papers (normalized_title);

CREATE TABLE source_requests (
    id SERIAL NOT NULL, 
    source VARCHAR(32) NOT NULL, 
    endpoint TEXT NOT NULL, 
    status_code INTEGER, 
    duration_ms INTEGER, 
    error TEXT, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE conjectures (
    id VARCHAR(36) NOT NULL, 
    slug VARCHAR(200) NOT NULL, 
    title TEXT NOT NULL, 
    field VARCHAR(64) NOT NULL, 
    subfields JSONB NOT NULL, 
    problem_type VARCHAR(32) NOT NULL, 
    original_statement TEXT NOT NULL, 
    normalized_statement TEXT NOT NULL, 
    definitions JSONB NOT NULL, 
    notation TEXT, 
    source_paper_id VARCHAR(36), 
    source_passage TEXT, 
    source_page INTEGER, 
    source_section TEXT, 
    source_candidate_id VARCHAR(36), 
    known_results JSONB NOT NULL, 
    potential_approaches JSONB NOT NULL, 
    relevant_theorems JSONB NOT NULL, 
    status VARCHAR(24) NOT NULL, 
    verification_confidence FLOAT, 
    status_is_manual_override BOOLEAN NOT NULL, 
    difficulty_estimate VARCHAR(32), 
    difficulty_rationale TEXT, 
    created_by VARCHAR(128) NOT NULL, 
    extraction_details JSONB NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(source_paper_id) REFERENCES papers (id) ON DELETE SET NULL, 
    UNIQUE (slug)
);

CREATE INDEX ix_conjectures_field ON conjectures (field);

CREATE INDEX ix_conjectures_source_paper_id ON conjectures (source_paper_id);

CREATE INDEX ix_conjectures_status ON conjectures (status);

CREATE TABLE paper_pages (
    id SERIAL NOT NULL, 
    paper_id VARCHAR(36) NOT NULL, 
    page_number INTEGER NOT NULL, 
    text TEXT NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(paper_id) REFERENCES papers (id) ON DELETE CASCADE, 
    UNIQUE (paper_id, page_number)
);

CREATE TABLE relationships (
    id VARCHAR(36) NOT NULL, 
    relation_type VARCHAR(32) NOT NULL, 
    from_type VARCHAR(16) NOT NULL, 
    from_id VARCHAR(36) NOT NULL, 
    to_type VARCHAR(16) NOT NULL, 
    to_id VARCHAR(36), 
    to_external TEXT, 
    source_paper_id VARCHAR(36), 
    created_by VARCHAR(128) NOT NULL, 
    verification_status VARCHAR(24) NOT NULL, 
    note TEXT, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(source_paper_id) REFERENCES papers (id) ON DELETE SET NULL
);

CREATE INDEX ix_relationships_from_id ON relationships (from_id);

CREATE INDEX ix_relationships_to_id ON relationships (to_id);

CREATE TABLE candidate_passages (
    id VARCHAR(36) NOT NULL, 
    paper_id VARCHAR(36) NOT NULL, 
    page_number INTEGER, 
    section TEXT, 
    origin VARCHAR(16) NOT NULL, 
    label TEXT, 
    char_start INTEGER NOT NULL, 
    passage TEXT NOT NULL, 
    context_before TEXT, 
    context_after TEXT, 
    trigger TEXT, 
    kind VARCHAR(32) NOT NULL, 
    detector VARCHAR(128) NOT NULL, 
    score FLOAT, 
    review_status VARCHAR(16) NOT NULL, 
    review_note TEXT, 
    llm_assessment JSONB, 
    conjecture_id VARCHAR(36), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(conjecture_id) REFERENCES conjectures (id) ON DELETE SET NULL, 
    FOREIGN KEY(paper_id) REFERENCES papers (id) ON DELETE CASCADE, 
    UNIQUE (paper_id, origin, char_start, detector)
);

CREATE INDEX ix_candidate_passages_paper_id ON candidate_passages (paper_id);

CREATE TABLE conjecture_events (
    id VARCHAR(36) NOT NULL, 
    conjecture_id VARCHAR(36) NOT NULL, 
    event_type VARCHAR(32) NOT NULL, 
    actor VARCHAR(128) NOT NULL, 
    summary TEXT NOT NULL, 
    previous_status VARCHAR(24), 
    new_status VARCHAR(24), 
    evidence JSONB NOT NULL, 
    details JSONB NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(conjecture_id) REFERENCES conjectures (id) ON DELETE CASCADE
);

CREATE INDEX ix_conjecture_events_conjecture_id ON conjecture_events (conjecture_id);

CREATE TABLE research_runs (
    id VARCHAR(36) NOT NULL, 
    conjecture_id VARCHAR(36) NOT NULL, 
    status VARCHAR(16) NOT NULL, 
    limits JSONB NOT NULL, 
    iteration INTEGER NOT NULL, 
    checkpoint JSONB NOT NULL, 
    report_markdown TEXT, 
    error TEXT, 
    started_at TIMESTAMP WITH TIME ZONE, 
    finished_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(conjecture_id) REFERENCES conjectures (id) ON DELETE CASCADE
);

CREATE INDEX ix_research_runs_conjecture_id ON research_runs (conjecture_id);

CREATE TABLE agent_tasks (
    id VARCHAR(36) NOT NULL, 
    research_run_id VARCHAR(36) NOT NULL, 
    agent_role VARCHAR(48) NOT NULL, 
    iteration INTEGER NOT NULL, 
    status VARCHAR(16) NOT NULL, 
    current_task TEXT, 
    input JSONB NOT NULL, 
    output JSONB, 
    report_markdown TEXT, 
    error TEXT, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(research_run_id) REFERENCES research_runs (id) ON DELETE CASCADE
);

CREATE INDEX ix_agent_tasks_research_run_id ON agent_tasks (research_run_id);

CREATE TABLE experiments (
    id VARCHAR(36) NOT NULL, 
    conjecture_id VARCHAR(36), 
    research_run_id VARCHAR(36), 
    title TEXT NOT NULL, 
    problem TEXT NOT NULL, 
    code TEXT NOT NULL, 
    code_sha256 VARCHAR(64) NOT NULL, 
    library_script VARCHAR(128), 
    parameters JSONB NOT NULL, 
    settings JSONB NOT NULL, 
    status VARCHAR(16) NOT NULL, 
    exit_code INTEGER, 
    stdout TEXT, 
    stderr TEXT, 
    result JSONB, 
    runtime_seconds FLOAT, 
    environment JSONB NOT NULL, 
    result_kind VARCHAR(32) NOT NULL, 
    interpretation TEXT, 
    created_by VARCHAR(128) NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE, 
    finished_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(conjecture_id) REFERENCES conjectures (id) ON DELETE SET NULL, 
    FOREIGN KEY(research_run_id) REFERENCES research_runs (id) ON DELETE SET NULL
);

CREATE INDEX ix_experiments_conjecture_id ON experiments (conjecture_id);

CREATE TABLE proof_attempts (
    id VARCHAR(36) NOT NULL, 
    conjecture_id VARCHAR(36) NOT NULL, 
    research_run_id VARCHAR(36), 
    strategy TEXT NOT NULL, 
    argument TEXT NOT NULL, 
    lemma_claim_ids JSONB NOT NULL, 
    known_gaps JSONB NOT NULL, 
    reviewer_feedback JSONB NOT NULL, 
    validation_level INTEGER NOT NULL, 
    status VARCHAR(24) NOT NULL, 
    lean_artifact JSONB, 
    created_by VARCHAR(128) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(conjecture_id) REFERENCES conjectures (id) ON DELETE CASCADE, 
    FOREIGN KEY(research_run_id) REFERENCES research_runs (id) ON DELETE SET NULL
);

CREATE INDEX ix_proof_attempts_conjecture_id ON proof_attempts (conjecture_id);

CREATE TABLE claims (
    id VARCHAR(36) NOT NULL, 
    conjecture_id VARCHAR(36), 
    research_run_id VARCHAR(36), 
    statement TEXT NOT NULL, 
    claim_type VARCHAR(32) NOT NULL, 
    validation_level INTEGER NOT NULL, 
    verification_status VARCHAR(24) NOT NULL, 
    evidence JSONB NOT NULL, 
    source_paper_id VARCHAR(36), 
    experiment_id VARCHAR(36), 
    created_by VARCHAR(128) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(conjecture_id) REFERENCES conjectures (id) ON DELETE CASCADE, 
    FOREIGN KEY(experiment_id) REFERENCES experiments (id) ON DELETE SET NULL, 
    FOREIGN KEY(research_run_id) REFERENCES research_runs (id) ON DELETE SET NULL, 
    FOREIGN KEY(source_paper_id) REFERENCES papers (id) ON DELETE SET NULL
);

CREATE INDEX ix_claims_conjecture_id ON claims (conjecture_id);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;


-- Deny direct client access through Supabase's auto-generated REST API.
DO $$ DECLARE t text; BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
  END LOOP;
END $$;
