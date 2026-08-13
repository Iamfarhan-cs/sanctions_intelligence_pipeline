CREATE TABLE acquisition_runs (
    run_id VARCHAR(100) PRIMARY KEY,
    source_id VARCHAR(100) NOT NULL
        REFERENCES sources(source_id),

    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,

    status VARCHAR(20) NOT NULL
        CHECK (status IN ('SUCCESS', 'FAILED', 'QUARANTINED')),

    acquisition_method VARCHAR(50) NOT NULL,
    http_status_code INTEGER,

    retry_count INTEGER NOT NULL DEFAULT 0
        CHECK (retry_count >= 0),

    error_type VARCHAR(100),
    error_message TEXT
);


CREATE TABLE artifacts (
    artifact_id VARCHAR(100) PRIMARY KEY,
    run_id VARCHAR(100) NOT NULL
        REFERENCES acquisition_runs(run_id),

    file_name TEXT NOT NULL,
    file_format VARCHAR(20) NOT NULL,
    file_size_bytes BIGINT NOT NULL
        CHECK (file_size_bytes >= 0),

    checksum VARCHAR(64) NOT NULL,
    checksum_algorithm VARCHAR(20) NOT NULL DEFAULT 'SHA-256',

    storage_bucket VARCHAR(100) NOT NULL,
    storage_key TEXT NOT NULL,

    source_version VARCHAR(255),
    acquired_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE validation_results (
    validation_id VARCHAR(100) PRIMARY KEY,
    artifact_id VARCHAR(100) NOT NULL
        REFERENCES artifacts(artifact_id),

    validation_status VARCHAR(20) NOT NULL
        CHECK (validation_status IN ('VALID', 'INVALID')),

    validation_errors TEXT,
    record_count BIGINT
        CHECK (record_count >= 0),

    validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE INDEX idx_acquisition_runs_source_started
    ON acquisition_runs(source_id, started_at);

CREATE INDEX idx_acquisition_runs_started
    ON acquisition_runs(started_at);

CREATE INDEX idx_artifacts_checksum
    ON artifacts(checksum);

CREATE INDEX idx_artifacts_storage_location
    ON artifacts(storage_bucket, storage_key);

CREATE INDEX idx_validation_results_artifact
    ON validation_results(artifact_id);