CREATE TABLE quarantine_events (
    quarantine_id VARCHAR(100) PRIMARY KEY,
    artifact_id VARCHAR(100) NOT NULL,
    reason TEXT NOT NULL,
    quarantine_bucket VARCHAR(100) NOT NULL,
    quarantine_key TEXT NOT NULL,
    quarantine_checksum VARCHAR(255) NOT NULL,
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT quarantine_events_artifact_id_fkey
        FOREIGN KEY (artifact_id)
        REFERENCES artifacts(artifact_id)
);