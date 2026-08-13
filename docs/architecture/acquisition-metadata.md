
# Acquisition Metadata Catalog

## Purpose

The Acquisition Metadata Catalog records what happened during every
sanctions-data acquisition attempt.

The catalog provides a traceable link between:

Source → Acquisition Run → Downloaded Artifact → Validation → Storage

It will allow the platform to answer:

- What source was contacted?
- When was it contacted?
- What artifact was received?
- Where did the artifact come from?
- How large was it?
- What format was it?
- What was its SHA-256 checksum?
- Was the acquisition successful?
- Where was the artifact stored?
- If the acquisition failed, what went wrong?

---

## 1. Source Information

These fields identify the authoritative source involved in the
acquisition.

| Field       | Purpose                            |
| ----------- | ---------------------------------- |
| source_id   | Internal identifier for the source |
| source_name | Human-readable source name         |
| source_url  | URL used to obtain the data        |
| source_type | API, download, feed, etc.          |

Example:

source_id = ofac
source_name = OFAC
source_type = download

---

## 2. Acquisition Run Information

These fields describe one acquisition attempt.

| Field              | Purpose                                       |
| ------------------ | --------------------------------------------- |
| run_id             | Unique identifier for the acquisition attempt |
| started_at         | Time the acquisition started                  |
| completed_at       | Time the acquisition finished                 |
| duration_seconds   | Total acquisition duration                    |
| acquisition_method | API, HTTP download, etc.                      |
| status             | Result of the acquisition                     |
| http_status_code   | HTTP response status when applicable          |

A run represents an attempt, not necessarily a successful download.

Example:

run_id = 20260813T080000Z-0001
status = SUCCESS

---

## 3. Artifact Information

These fields describe the actual file or object obtained from the
source.

| Field           | Purpose                                     |
| --------------- | ------------------------------------------- |
| artifact_id     | Unique identifier for the acquired artifact |
| file_name       | Original file name when available           |
| file_format     | XML, JSON, CSV, etc.                        |
| file_size_bytes | Size of the artifact                        |
| storage_bucket  | MinIO bucket containing the artifact        |
| storage_key     | Object path/key inside MinIO                |

Example:

artifact_id = 7f8c...
file_name = source-data.xml
file_format = XML
storage_bucket = sanctions-raw
storage_key = ofac/2026/08/13/source-data.xml

---

## 4. Integrity Information

Integrity metadata allows us to identify identical artifacts and
verify that stored data has not unexpectedly changed.

| Field              | Purpose                                 |
| ------------------ | --------------------------------------- |
| checksum           | Hash of the acquired artifact           |
| checksum_algorithm | Algorithm used to generate the checksum |

Initial algorithm:

SHA-256

Example:

checksum_algorithm = SHA-256
checksum = <64-character hexadecimal hash>

The checksum will also help with duplicate detection.

---

## 5. Validation Information

These fields describe what happened after the artifact was acquired.

| Field             | Purpose                                        |
| ----------------- | ---------------------------------------------- |
| validation_status | Result of validation                           |
| validation_errors | Validation problems, if any                    |
| record_count      | Number of records when successfully determined |

Possible validation outcomes will be refined as the source schemas
are implemented.

Examples:

VALID
INVALID
QUARANTINED

---

## 6. Failure Information

Failed acquisitions must not disappear silently.

| Field         | Purpose                          |
| ------------- | -------------------------------- |
| error_type    | Category of failure              |
| error_message | Human-readable error description |
| retry_count   | Number of acquisition retries    |
| failed_at     | Time of failure                  |

Examples of failure categories:

- network failure
- HTTP failure
- timeout
- invalid response
- malformed artifact
- validation failure

---

## 7. Provenance Information

The catalog must preserve enough information to trace an artifact back
to the acquisition that produced it.

| Field            | Purpose                                |
| ---------------- | -------------------------------------- |
| source_id        | Source that produced the artifact      |
| run_id           | Acquisition run that produced it       |
| acquired_at      | Time the artifact was acquired         |
| pipeline_version | Version of the acquisition code        |
| source_version   | Source-provided version when available |

`source_version` must only be populated when the source actually
provides a meaningful version or equivalent identifier.

We must not invent source versions.

---

## 8. Conceptual Relationship

The metadata relationships are:

Source
  |
  | 1-to-many
  ↓
Acquisition Run
  |
  | produces
  ↓
Artifact
  |
  ├── Validation Result
  └── MinIO Object

Conceptually:

SOURCE
  ↓
ACQUISITION RUN
  ↓
ARTIFACT
  ↓
VALIDATION
  ↓
STORAGE

---

## 9. Example Successful Acquisition

An acquisition could eventually produce metadata conceptually similar
to:

source_id:
    ofac

run_id:
    20260813T080000Z-0001

started_at:
    2026-08-13T08:00:00Z

completed_at:
    2026-08-13T08:00:07Z

status:
    SUCCESS

file_name:
    source-data.xml

file_format:
    XML

file_size_bytes:
    582341

checksum_algorithm:
    SHA-256

checksum:
    <calculated hash></calculated>

validation_status:
    VALID

storage_bucket:
    sanctions-raw

storage_key:
    ofac/2026/08/13/source-data.xml

---

## 10. Example Failed Acquisition

A failed acquisition should still create an acquisition record.

Example:

source_id:
    ofac

run_id:
    20260813T090000Z-0002

status:
    FAILED

error_type:
    TIMEOUT

error_message:
    Source request timed out

retry_count:
    3

artifact:
    NULL

This allows the platform to distinguish:

- no acquisition was attempted
- acquisition was attempted and failed
- acquisition succeeded
- acquisition succeeded but validation failed

---

## 11. Important Design Principles

### 1. Every acquisition attempt should be traceable

A failed run is still useful operational information.

### 2. Metadata is separate from raw data

The raw artifact belongs in MinIO.

The acquisition metadata describes that artifact.

### 3. Raw artifacts remain unchanged

The acquisition layer should preserve the source artifact rather than
modifying its contents.

### 4. Checksums identify content

A checksum can help determine whether two acquired artifacts contain
identical bytes.

### 5. Source-provided versions are optional

We only record a source version when the source actually provides one.

### 6. Failures must be observable

An acquisition failure must be recorded rather than silently ignored.

### 7. The metadata model will evolve

The final schema will be refined after implementing the actual source
connectors and observing the metadata they provide.

---

## Current Scope

This document defines the conceptual metadata requirements.

It does NOT yet define:

- PostgreSQL tables
- SQL schema
- indexes
- primary-key implementation
- database migrations
- API contracts
- Kafka events

Those decisions will be made in later steps.



---

## Refined Conceptual Model

The acquisition metadata model separates the acquisition attempt from
the artifact produced by that attempt.

### Source

Identifies the authoritative source.

### Acquisition Run

Represents one attempt to acquire data from a source.

A run exists even when the acquisition fails.

### Artifact

Represents the actual source artifact obtained during a successful
acquisition.

An acquisition run may produce zero or one primary artifact in the
initial design.

### Validation

Represents the validation result associated with the acquired artifact.

### Storage

The artifact metadata records the MinIO bucket and object key where the
artifact is stored.

### Relationship

Source
  |
  | 1-to-many
  ↓
Acquisition Run
  |
  | 0-to-1
  ↓
Artifact
  |
  ↓
Validation
  |
  ↓
MinIO Object

This separation allows failed acquisition attempts to be recorded even
when no artifact exists.


---

## Metadata Catalog Storage Decision

### Decision

PostgreSQL will be used as the initial acquisition metadata catalog.

### Why PostgreSQL?

Acquisition metadata is structured relational information.

The catalog needs to support:

- relational relationships
- primary and foreign keys
- uniqueness constraints
- indexing
- transactional updates
- SQL queries
- duplicate detection
- operational reporting

PostgreSQL provides these capabilities while remaining open-source and
easy to run locally using Docker.

### Responsibility Separation

MinIO stores the actual source artifacts.

PostgreSQL stores metadata describing those artifacts.

#### MinIO

Responsible for:

- raw XML
- raw JSON
- raw CSV
- other source artifacts
- object versions
- object storage

#### PostgreSQL

Responsible for:

- source information
- acquisition runs
- artifact metadata
- checksums
- validation results
- acquisition status
- MinIO storage references
- provenance metadata

### Conceptual Architecture

Source
  |
  ↓
Acquisition
  |
  ├──────────────→ MinIO
  │                 |
  │                 └── Raw Artifact
  │
  └──────────────→ PostgreSQL
                    |
                    └── Acquisition Metadata

The raw artifact is not stored inside PostgreSQL.

PostgreSQL stores the information required to identify, query, and
trace the artifact in MinIO.

### Why Not Use MinIO as the Metadata Catalog?

MinIO is optimized for object storage.

The acquisition catalog requires relational querying, constraints,
relationships, and indexing.

Therefore, MinIO and PostgreSQL have complementary responsibilities
rather than replacing one another.


---

## Initial Relational Schema

The initial metadata catalog will use four core relational tables:

1. sources
2. acquisition_runs
3. artifacts
4. validation_results

### sources

Stores information about authoritative data sources.

Core concepts:

- source identifier
- source name
- source type
- source URL
- active status
- creation timestamp

### acquisition_runs

Represents one attempt to acquire data from a source.

Core concepts:

- run identifier
- source reference
- start and completion timestamps
- acquisition status
- acquisition method
- HTTP status
- retry count
- failure information

A failed acquisition run must still be recorded.

### artifacts

Represents an artifact successfully obtained during an acquisition run.

Core concepts:

- artifact identifier
- acquisition-run reference
- original file name
- file format
- file size
- checksum
- checksum algorithm
- MinIO bucket
- MinIO object key
- source version when available
- acquisition timestamp

### validation_results

Stores validation results associated with acquired artifacts.

Core concepts:

- validation identifier
- artifact reference
- validation status
- validation errors
- record count
- validation timestamp

### Relationships

sources
  |
  | 1:N
  ↓
acquisition_runs
  |
  | 0:1
  ↓
artifacts
  |
  | 1:N
  ↓
validation_results

The schema is intentionally limited to acquisition concerns.

Entity resolution, sanctions entities, aliases, addresses, sanctions
events, and alerts will be modeled in later tasks.


---

## Keys, Constraints and Indexing Strategy

### Primary Keys

Each metadata table will have its own primary key:

- sources.source_id
- acquisition_runs.run_id
- artifacts.artifact_id
- validation_results.validation_id

### Foreign Keys

The following relationships should be enforced:

- acquisition_runs.source_id → sources.source_id
- artifacts.run_id → acquisition_runs.run_id
- validation_results.artifact_id → artifacts.artifact_id

Foreign keys prevent orphaned metadata records.

### NOT NULL Constraints

Fields required for identifying and interpreting a record should be
non-null.

Fields that are legitimately unavailable should remain nullable.

For example:

- HTTP status may not exist after a connection failure.
- Source version may not be provided by a source.
- Error information should not be required for successful runs.

### Controlled Status Values

Acquisition and validation status values should be constrained to
defined states rather than arbitrary strings.

The exact database representation will be finalized during schema
implementation.

### Checksum

Checksums should not initially be globally unique.

The same artifact may legitimately be acquired more than once.

Checksum values will instead support duplicate-content detection.

### Initial Indexes

Candidate indexes include:

- acquisition_runs(source_id, started_at)
- acquisition_runs(started_at)
- artifacts(checksum)
- artifacts(storage_bucket, storage_key)

Indexes will be validated against actual query patterns before the
final schema is implemented.

### Indexing Principle

Indexes should be created to support real access patterns.

The database should not be indexed indiscriminately.
