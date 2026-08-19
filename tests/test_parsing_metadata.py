from datetime import datetime, timezone
from uuid import uuid4

from sanctions_pipeline.metadata.postgres import (
    create_acquisition_run,
    create_artifact,
    create_postgres_connection,
    create_validation_result,
    get_artifact_with_latest_validation,
)


def test_get_artifact_with_valid_validation():
    conn = create_postgres_connection()

    run_id = f"task9-meta-run-{uuid4().hex[:12]}"
    artifact_id = f"task9-meta-artifact-{uuid4().hex[:12]}"
    validation_id = f"task9-meta-validation-{uuid4().hex[:12]}"

    try:
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
            file_name="task9-test.json",
            file_format="json",
            file_size_bytes=100,
            checksum=(
                "c206464f523376ce8c5704a4729330832eabaa8a170d1e8ed9f83814f00196d2"
            ),
            storage_bucket="sanctions-raw",
            storage_key="task9-test.json",
        )

        create_validation_result(
            conn=conn,
            validation_id=validation_id,
            artifact_id=artifact_id,
            validation_status="VALID",
        )

        result = get_artifact_with_latest_validation(
            conn,
            artifact_id,
        )

        assert result is not None
        assert result["artifact_id"] == artifact_id
        assert result["run_id"] == run_id
        assert result["file_format"] == "json"
        assert result["storage_bucket"] == "sanctions-raw"
        assert result["storage_key"] == "task9-test.json"
        assert result["validation_status"] == "VALID"

    finally:
        with conn.cursor() as cursor:
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


def test_get_artifact_without_validation():
    conn = create_postgres_connection()

    run_id = f"task9-meta-run-{uuid4().hex[:12]}"
    artifact_id = f"task9-meta-artifact-{uuid4().hex[:12]}"

    try:
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
            file_name="task9-test.json",
            file_format="json",
            file_size_bytes=100,
            checksum=(
                "c206464f523376ce8c5704a4729330832eabaa8a170d1e8ed9f83814f00196d2"
            ),
            storage_bucket="sanctions-raw",
            storage_key="task9-test.json",
        )

        result = get_artifact_with_latest_validation(
            conn,
            artifact_id,
        )

        assert result is not None
        assert result["validation_status"] is None

    finally:
        with conn.cursor() as cursor:
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
