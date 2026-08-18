import hashlib
import os
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv

from sanctions_pipeline.metadata.postgres import (
    create_acquisition_run,
    create_artifact,
    create_postgres_connection,
    create_validation_result,
)
from sanctions_pipeline.quarantine.service import quarantine_artifact
from sanctions_pipeline.storage.minio_client import (
    create_minio_client,
    upload_file,
)

load_dotenv()


def test_quarantine_success(tmp_path):
    conn = create_postgres_connection()

    run_id = f"task8-test-run-{uuid4().hex[:12]}"
    artifact_id = f"task8-test-artifact-{uuid4().hex[:12]}"
    validation_id = f"task8-test-validation-{uuid4().hex[:12]}"

    source_bucket = os.environ["MINIO_BUCKET"]
    quarantine_bucket = "sanctions-quarantine"

    object_name = f"task-8-test/{uuid4().hex}/quarantine-test.txt"

    test_file = tmp_path / "quarantine-test.txt"
    test_file.write_text("Task 8 pytest quarantine test")

    checksum = hashlib.sha256(test_file.read_bytes()).hexdigest()

    try:
        create_acquisition_run(
            conn=conn,
            run_id=run_id,
            source_id="task8-test-source",
            started_at=datetime.now(timezone.utc),
            acquisition_method="TEST",
        )

        create_artifact(
            conn=conn,
            artifact_id=artifact_id,
            run_id=run_id,
            file_name=test_file.name,
            file_format="TXT",
            file_size_bytes=test_file.stat().st_size,
            checksum=checksum,
            storage_bucket=source_bucket,
            storage_key=object_name,
            source_version="task8-pytest",
        )

        create_validation_result(
            conn=conn,
            validation_id=validation_id,
            artifact_id=artifact_id,
            validation_status="INVALID",
            validation_errors="Task 8 pytest quarantine test",
            record_count=None,
        )

        minio_client = create_minio_client(
            endpoint=os.environ["MINIO_ENDPOINT"],
            access_key=os.environ["MINIO_ROOT_USER"],
            secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        )

        upload_file(
            client=minio_client,
            file_path=str(test_file),
            bucket_name=source_bucket,
            object_name=object_name,
        )

        quarantine_object = object_name

        quarantine_id = quarantine_artifact(
            conn=conn,
            minio_client=minio_client,
            artifact_id=artifact_id,
            run_id=run_id,
            source_bucket=source_bucket,
            source_object=object_name,
            quarantine_bucket=quarantine_bucket,
            quarantine_object=quarantine_object,
            reason="Task 8 pytest quarantine test",
            quarantine_checksum=checksum,
        )

        quarantine_stat = minio_client.stat_object(
            quarantine_bucket,
            quarantine_object,
        )

        assert quarantine_stat.size == test_file.stat().st_size

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    quarantine_id,
                    artifact_id,
                    reason,
                    quarantine_bucket,
                    quarantine_key,
                    quarantine_checksum
                FROM quarantine_events
                WHERE quarantine_id = %s
                """,
                (quarantine_id,),
            )

            quarantine_result = cursor.fetchone()

            cursor.execute(
                """
                SELECT status
                FROM acquisition_runs
                WHERE run_id = %s
                """,
                (run_id,),
            )

            run_result = cursor.fetchone()

        assert quarantine_result is not None
        assert quarantine_result[0] == quarantine_id
        assert quarantine_result[1] == artifact_id
        assert quarantine_result[2] == "Task 8 pytest quarantine test"
        assert quarantine_result[3] == quarantine_bucket
        assert quarantine_result[4] == quarantine_object
        assert quarantine_result[5].lower() == checksum.lower()

        assert run_result is not None
        assert run_result[0] == "QUARANTINED"

    finally:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM quarantine_events WHERE artifact_id = %s",
                (artifact_id,),
            )
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
        conn.close()

        try:
            minio_client.remove_object(
                quarantine_bucket,
                quarantine_object,
            )
            minio_client.remove_object(
                source_bucket,
                object_name,
            )
        except Exception:
            pass

def test_quarantine_checksum_mismatch(tmp_path):
    conn = create_postgres_connection()

    run_id = f"task8-test-run-{uuid4().hex[:12]}"
    artifact_id = f"task8-test-artifact-{uuid4().hex[:12]}"
    validation_id = f"task8-test-validation-{uuid4().hex[:12]}"

    source_bucket = os.environ["MINIO_BUCKET"]
    quarantine_bucket = "sanctions-quarantine"

    object_name = f"task-8-test/{uuid4().hex}/quarantine-failure-test.txt"

    test_file = tmp_path / "quarantine-failure-test.txt"
    test_file.write_text("Task 8 pytest checksum failure test")

    checksum = hashlib.sha256(test_file.read_bytes()).hexdigest()
    wrong_checksum = "0" * 64

    try:
        create_acquisition_run(
            conn=conn,
            run_id=run_id,
            source_id="task8-test-source",
            started_at=datetime.now(timezone.utc),
            acquisition_method="TEST",
        )

        create_artifact(
            conn=conn,
            artifact_id=artifact_id,
            run_id=run_id,
            file_name=test_file.name,
            file_format="TXT",
            file_size_bytes=test_file.stat().st_size,
            checksum=checksum,
            storage_bucket=source_bucket,
            storage_key=object_name,
            source_version="task8-pytest",
        )

        create_validation_result(
            conn=conn,
            validation_id=validation_id,
            artifact_id=artifact_id,
            validation_status="INVALID",
            validation_errors="Task 8 pytest checksum failure test",
            record_count=None,
        )

        minio_client = create_minio_client(
            endpoint=os.environ["MINIO_ENDPOINT"],
            access_key=os.environ["MINIO_ROOT_USER"],
            secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        )

        upload_file(
            client=minio_client,
            file_path=str(test_file),
            bucket_name=source_bucket,
            object_name=object_name,
        )

        quarantine_object = object_name

        import pytest

        with pytest.raises(ValueError, match="Quarantine checksum mismatch"):
            quarantine_artifact(
                conn=conn,
                minio_client=minio_client,
                artifact_id=artifact_id,
                run_id=run_id,
                source_bucket=source_bucket,
                source_object=object_name,
                quarantine_bucket=quarantine_bucket,
                quarantine_object=quarantine_object,
                reason="Task 8 pytest checksum failure test",
                quarantine_checksum=wrong_checksum,
            )

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM quarantine_events
                WHERE artifact_id = %s
                """,
                (artifact_id,),
            )

            quarantine_count = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT status
                FROM acquisition_runs
                WHERE run_id = %s
                """,
                (run_id,),
            )

            run_result = cursor.fetchone()

        assert quarantine_count == 0
        assert run_result is not None
        assert run_result[0] == "SUCCESS"

    finally:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM quarantine_events WHERE artifact_id = %s",
                (artifact_id,),
            )
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
        conn.close()

        try:
            minio_client.remove_object(
                quarantine_bucket,
                quarantine_object,
            )
            minio_client.remove_object(
                source_bucket,
                object_name,
            )
        except Exception:
            pass
