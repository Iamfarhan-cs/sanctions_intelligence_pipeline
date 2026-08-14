from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sanctions_pipeline.acquisition.downloader import download_file
from sanctions_pipeline.metadata.postgres import (
    create_acquisition_run,
    create_artifact,
    create_postgres_connection,
    update_acquisition_run,
)
from sanctions_pipeline.storage.minio_client import (
    create_minio_client,
    upload_file,
)


def acquire_source(
    source_id: str,
    source_url: str,
    source_version: str | None,
    minio_endpoint: str,
    minio_access_key: str,
    minio_secret_key: str,
    minio_bucket: str,
    storage_key: str,
    output_path: str,
) -> str:
    """
    Acquire a source artifact and register its metadata.

    Returns:
        Acquisition run ID.
    """

    run_id = str(uuid4())
    started_at = datetime.now(timezone.utc)

    conn = create_postgres_connection()

    create_acquisition_run(
        conn=conn,
        run_id=run_id,
        source_id=source_id,
        started_at=started_at,
        acquisition_method="HTTP_DOWNLOAD",
    )

    try:
        file_path, checksum = download_file(
            url=source_url,
            output_path=output_path,
        )

        file_size = Path(file_path).stat().st_size

        minio_client = create_minio_client(
            endpoint=minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
        )

        upload_file(
            client=minio_client,
            file_path=str(file_path),
            bucket_name=minio_bucket,
            object_name=storage_key,
        )

        file_format = Path(file_path).suffix.lstrip(".").upper() or "UNKNOWN"

        artifact_id = str(uuid4())

        create_artifact(
            conn=conn,
            artifact_id=artifact_id,
            run_id=run_id,
            file_name=Path(file_path).name,
            file_format=file_format,
            file_size_bytes=file_size,
            checksum=checksum,
            storage_bucket=minio_bucket,
            storage_key=storage_key,
            source_version=source_version,
        )

        update_acquisition_run(
            conn=conn,
            run_id=run_id,
            status="SUCCESS",
            completed_at=datetime.now(timezone.utc),
            http_status_code=200,
            retry_count=0,
        )

        return run_id

    except Exception as exc:
        update_acquisition_run(
            conn=conn,
            run_id=run_id,
            status="FAILED",
            completed_at=datetime.now(timezone.utc),
            retry_count=0,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

        raise

    finally:
        conn.close()