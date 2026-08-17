from datetime import datetime, timezone
from uuid import uuid4

from sanctions_pipeline.metadata.postgres import (
    create_acquisition_run,
    create_artifact,
    create_postgres_connection,
    create_validation_result,
)


def test_create_validation_result():
    conn = create_postgres_connection()

    run_id = f"task7-test-run-{uuid4().hex[:12]}"
    artifact_id = f"task7-test-artifact-{uuid4().hex[:12]}"
    validation_id = f"task7-test-validation-{uuid4().hex[:12]}"

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
            file_name="task7-test.xml",
            file_format="xml",
            file_size_bytes=100,
            checksum="c206464f523376ce8c5704a4729330832eabaa8a170d1e8ed9f83814f00196d2",
            storage_bucket="test-bucket",
            storage_key="task7-test.xml",
        )

        create_validation_result(
            conn=conn,
            validation_id=validation_id,
            artifact_id=artifact_id,
            validation_status="VALID",
            validation_errors=None,
            record_count=None,
        )

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    validation_id,
                    artifact_id,
                    validation_status,
                    validation_errors,
                    record_count
                FROM validation_results
                WHERE validation_id = %s
                """,
                (validation_id,),
            )

            result = cursor.fetchone()

        assert result is not None
        assert result[0] == validation_id
        assert result[1] == artifact_id
        assert result[2] == "VALID"
        assert result[3] is None
        assert result[4] is None

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


def test_create_invalid_validation_result():
    conn = create_postgres_connection()

    run_id = f"task7-test-run-{uuid4().hex[:12]}"
    artifact_id = f"task7-test-artifact-{uuid4().hex[:12]}"
    validation_id = f"task7-test-validation-{uuid4().hex[:12]}"

    validation_errors = (
        "Checksum mismatch. Expected abc, got def."
    )

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
            file_name="task7-invalid.xml",
            file_format="xml",
            file_size_bytes=100,
            checksum="c206464f523376ce8c5704a4729330832eabaa8a170d1e8ed9f83814f00196d2",
            storage_bucket="test-bucket",
            storage_key="task7-invalid.xml",
        )

        create_validation_result(
            conn=conn,
            validation_id=validation_id,
            artifact_id=artifact_id,
            validation_status="INVALID",
            validation_errors=validation_errors,
            record_count=None,
        )

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    validation_id,
                    artifact_id,
                    validation_status,
                    validation_errors,
                    record_count
                FROM validation_results
                WHERE validation_id = %s
                """,
                (validation_id,),
            )

            result = cursor.fetchone()

        assert result is not None
        assert result[0] == validation_id
        assert result[1] == artifact_id
        assert result[2] == "INVALID"
        assert result[3] == validation_errors
        assert result[4] is None

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