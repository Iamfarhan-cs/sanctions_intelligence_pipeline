import os
import uuid
from datetime import datetime, timezone

import pytest

from sanctions_pipeline.metadata.postgres import (
    create_acquisition_run,
    create_artifact,
    create_postgres_connection,
    create_validation_result,
)
from sanctions_pipeline.parsing.orchestrator import parse_validated_artifact
from sanctions_pipeline.parsing.parser import ParserError
from sanctions_pipeline.storage.minio_client import (
    create_minio_client,
    upload_file,
)


@pytest.fixture
def postgres_connection():
    conn = create_postgres_connection()

    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def minio_client():
    return create_minio_client(
        endpoint=os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
    )


def create_test_run_and_artifact(
    conn,
    *,
    run_id,
    artifact_id,
    file_name,
    file_format,
    storage_bucket,
    storage_key,
):
    create_acquisition_run(
        conn=conn,
        run_id=run_id,
        source_id="task6-test-source",
        started_at=datetime.now(timezone.utc),
        acquisition_method="TEST",
    )

    create_artifact(
        conn=conn,
        artifact_id=artifact_id,
        run_id=run_id,
        file_name=file_name,
        file_format=file_format,
        file_size_bytes=100,
        checksum=(
            "c206464f523376ce8c5704a4729330832eabaa8a170d1e8ed9f83814f00196d2"
        ),
        storage_bucket=storage_bucket,
        storage_key=storage_key,
    )


def cleanup_database(
    conn,
    *,
    validation_id,
    artifact_id,
    run_id,
):
    with conn.cursor() as cursor:
        if validation_id is not None:
            cursor.execute(
                "DELETE FROM validation_results WHERE validation_id = %s",
                (validation_id,),
            )

        cursor.execute(
            "DELETE FROM artifacts WHERE artifact_id = %s",
            (artifact_id,),
        )

        cursor.execute(
            "DELETE FROM acquisition_runs WHERE run_id = %s",
            (run_id,),
        )

    conn.commit()


def test_parse_validated_json_artifact(
    postgres_connection,
    minio_client,
    tmp_path,
):
    conn = postgres_connection

    run_id = f"task9-e2e-run-{uuid.uuid4().hex[:12]}"
    artifact_id = f"task9-e2e-artifact-{uuid.uuid4().hex[:12]}"
    validation_id = f"task9-e2e-validation-{uuid.uuid4().hex[:12]}"

    bucket = os.environ["MINIO_BUCKET"]
    object_name = f"task-9/e2e/{uuid.uuid4()}/sanctions.json"

    local_artifact = tmp_path / "sanctions.json"

    local_artifact.write_text(
        '{"name": "Example", "country": "US"}',
        encoding="utf-8",
    )

    create_test_run_and_artifact(
        conn,
        run_id=run_id,
        artifact_id=artifact_id,
        file_name="sanctions.json",
        file_format="json",
        storage_bucket=bucket,
        storage_key=object_name,
    )

    create_validation_result(
        conn=conn,
        validation_id=validation_id,
        artifact_id=artifact_id,
        validation_status="VALID",
    )

    upload_file(
        minio_client,
        str(local_artifact),
        bucket,
        object_name,
    )

    try:
        result = parse_validated_artifact(
            conn,
            minio_client,
            artifact_id=artifact_id,
            source_id="task6-test-source",
        )

        assert result.artifact_id == artifact_id
        assert result.run_id == run_id
        assert result.source_id == "task6-test-source"
        assert result.file_format == "json"

        assert len(result.records) == 1
        assert result.records[0].record_index == 0
        assert result.records[0].data == {
            "name": "Example",
            "country": "US",
        }

    finally:
        minio_client.remove_object(
            bucket,
            object_name,
        )

        cleanup_database(
            conn,
            validation_id=validation_id,
            artifact_id=artifact_id,
            run_id=run_id,
        )


def test_invalid_artifact_is_not_parsed(
    postgres_connection,
    minio_client,
    tmp_path,
):
    conn = postgres_connection

    run_id = f"task9-e2e-run-{uuid.uuid4().hex[:12]}"
    artifact_id = f"task9-e2e-artifact-{uuid.uuid4().hex[:12]}"
    validation_id = f"task9-e2e-validation-{uuid.uuid4().hex[:12]}"

    bucket = os.environ["MINIO_BUCKET"]
    object_name = f"task-9/e2e/{uuid.uuid4()}/invalid.json"

    local_artifact = tmp_path / "invalid.json"

    local_artifact.write_text(
        '{"name": "Invalid"}',
        encoding="utf-8",
    )

    create_test_run_and_artifact(
        conn,
        run_id=run_id,
        artifact_id=artifact_id,
        file_name="invalid.json",
        file_format="json",
        storage_bucket=bucket,
        storage_key=object_name,
    )

    create_validation_result(
        conn=conn,
        validation_id=validation_id,
        artifact_id=artifact_id,
        validation_status="INVALID",
        validation_errors="Checksum mismatch.",
    )

    upload_file(
        minio_client,
        str(local_artifact),
        bucket,
        object_name,
    )

    try:
        with pytest.raises(
            ParserError,
            match="not eligible for parsing",
        ):
            parse_validated_artifact(
                conn,
                minio_client,
                artifact_id=artifact_id,
                source_id="task6-test-source",
            )

    finally:
        minio_client.remove_object(
            bucket,
            object_name,
        )

        cleanup_database(
            conn,
            validation_id=validation_id,
            artifact_id=artifact_id,
            run_id=run_id,
        )


def test_artifact_without_validation_is_not_parsed(
    postgres_connection,
    minio_client,
):
    conn = postgres_connection

    run_id = f"task9-e2e-run-{uuid.uuid4().hex[:12]}"
    artifact_id = f"task9-e2e-artifact-{uuid.uuid4().hex[:12]}"

    bucket = os.environ["MINIO_BUCKET"]
    object_name = f"task-9/e2e/{uuid.uuid4()}/unvalidated.json"

    create_test_run_and_artifact(
        conn,
        run_id=run_id,
        artifact_id=artifact_id,
        file_name="unvalidated.json",
        file_format="json",
        storage_bucket=bucket,
        storage_key=object_name,
    )

    try:
        with pytest.raises(
            ParserError,
            match="not eligible for parsing",
        ):
            parse_validated_artifact(
                conn,
                minio_client,
                artifact_id=artifact_id,
                source_id="task6-test-source",
            )

    finally:
        cleanup_database(
            conn,
            validation_id=None,
            artifact_id=artifact_id,
            run_id=run_id,
        )
