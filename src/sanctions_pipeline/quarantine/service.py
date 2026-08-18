import hashlib
from datetime import datetime, timezone
from uuid import uuid4

from sanctions_pipeline.metadata.postgres import (
    create_quarantine_event,
    update_acquisition_run,
)
from sanctions_pipeline.storage.minio_client import (
    copy_object,
    read_object,
    stat_object,
)


def quarantine_artifact(
    conn,
    minio_client,
    artifact_id: str,
    run_id: str,
    source_bucket: str,
    source_object: str,
    quarantine_bucket: str,
    quarantine_object: str,
    reason: str,
    quarantine_checksum: str,
) -> str:
    """
    Quarantine an invalid artifact and record its lineage.

    Returns:
        Quarantine event ID.
    """

    quarantine_id = str(uuid4())

    copy_object(
        client=minio_client,
        source_bucket=source_bucket,
        source_object=source_object,
        destination_bucket=quarantine_bucket,
        destination_object=quarantine_object,
    )

    stat_object(
        client=minio_client,
        bucket_name=quarantine_bucket,
        object_name=quarantine_object,
    )

    quarantine_data = read_object(
        client=minio_client,
        bucket_name=quarantine_bucket,
        object_name=quarantine_object,
    )

    actual_checksum = hashlib.sha256(quarantine_data).hexdigest()

    if actual_checksum.lower() != quarantine_checksum.lower():
        raise ValueError(
            "Quarantine checksum mismatch: "
            f"expected {quarantine_checksum}, got {actual_checksum}"
        )

    create_quarantine_event(
        conn=conn,
        quarantine_id=quarantine_id,
        artifact_id=artifact_id,
        reason=reason,
        quarantine_bucket=quarantine_bucket,
        quarantine_key=quarantine_object,
        quarantine_checksum=actual_checksum,
    )

    update_acquisition_run(
        conn=conn,
        run_id=run_id,
        status="QUARANTINED",
        completed_at=datetime.now(timezone.utc),
        retry_count=0,
    )

    return quarantine_id
