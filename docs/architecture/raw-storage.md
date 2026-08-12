
# Raw Storage Architecture

## Purpose

MinIO provides the object-storage layer for the Sanctions Intelligence
Data Platform.

The raw storage layer preserves source artifacts before normalization
or transformation.

This allows the platform to support:

- historical reconstruction
- reproducibility
- debugging
- data lineage
- source comparison
- reprocessing

## Storage Buckets

### sanctions-raw

Stores successfully acquired and technically validated source artifacts.

Expected sources:

- OFAC
- UK
- EU
- UN

Versioning is enabled on this bucket.

### sanctions-quarantine

Stores artifacts that fail technical validation and therefore must not
enter the trusted raw-data layer.

### sanctions-metadata

Stores acquisition-related metadata and manifests.

## Logical Object Structure

The planned object-key convention is:

<source>/<dataset>/<YYYY>/<MM>/<DD>/<artifact>

Example:

ofac/sdn/2026/08/12/sdn.xml

The date-based path is for organization and discovery. The content
identity will be established separately through SHA-256 hashing and
acquisition metadata.

## Versioning

Versioning is enabled on `sanctions-raw`.

This provides an additional protection mechanism against accidental
replacement of raw source artifacts.

The application will also maintain its own acquisition and artifact
metadata rather than relying solely on MinIO object-version IDs.

## Persistence

MinIO runs inside Docker.

Its `/data` directory is backed by a persistent Docker volume:

minio_data

This ensures that removing and recreating the MinIO container does not
remove the stored objects.

## Data Flow

Authoritative Source
        |
        v
Future Acquisition Layer
        |
        v
Technical Validation
        |
        +---- invalid ----> sanctions-quarantine
        |
        v
SHA-256
        |
        v
sanctions-raw
        |
        v
Future Normalization Layer

## Current Implementation

The following infrastructure has been implemented locally:

- Docker
- Docker Compose
- MinIO
- Persistent Docker volume
- sanctions-raw bucket
- sanctions-quarantine bucket
- sanctions-metadata bucket
- Versioning on sanctions-raw

No real sanctions source data is currently being ingested.

Real source acquisition will be implemented in a later task.
