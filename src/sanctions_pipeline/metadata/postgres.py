import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


def create_postgres_connection() -> psycopg.Connection:
    """
    Create a PostgreSQL connection using environment configuration.
    """

    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "sanctions"),
        user=os.getenv("POSTGRES_USER", "sanctions"),
        password=os.environ["POSTGRES_PASSWORD"],
    )


def create_acquisition_run(
    conn,
    run_id: str,
    source_id: str,
    started_at,
    acquisition_method: str,
) -> None:
    """
    Create an acquisition run record.
    """

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO acquisition_runs (
                run_id,
                source_id,
                started_at,
                status,
                acquisition_method,
                retry_count
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                run_id,
                source_id,
                started_at,
                "SUCCESS",
                acquisition_method,
                0,
            ),
        )

    conn.commit()



def create_artifact(
    conn,
    artifact_id: str,
    run_id: str,
    file_name: str,
    file_format: str,
    file_size_bytes: int,
    checksum: str,
    storage_bucket: str,
    storage_key: str,
    source_version: str | None = None,
) -> None:
    """
    Register an acquired artifact in PostgreSQL.
    """

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO artifacts (
                artifact_id,
                run_id,
                file_name,
                file_format,
                file_size_bytes,
                checksum,
                checksum_algorithm,
                storage_bucket,
                storage_key,
                source_version
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                artifact_id,
                run_id,
                file_name,
                file_format,
                file_size_bytes,
                checksum,
                "SHA-256",
                storage_bucket,
                storage_key,
                source_version,
            ),
        )

    conn.commit()


def update_acquisition_run(
    conn,
    run_id: str,
    status: str,
    completed_at,
    http_status_code: int | None = None,
    retry_count: int = 0,
    error_type: str | None = None,
    error_message: str | None = None,
) -> None:
    """
    Update the final state of an acquisition run.
    """

    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE acquisition_runs
            SET
                completed_at = %s,
                status = %s,
                http_status_code = %s,
                retry_count = %s,
                error_type = %s,
                error_message = %s
            WHERE run_id = %s
            """,
            (
                completed_at,
                status,
                http_status_code,
                retry_count,
                error_type,
                error_message,
                run_id,
            ),
        )

    conn.commit()


def create_validation_result(
    conn,
    validation_id: str,
    artifact_id: str,
    validation_status: str,
    validation_errors: str | None = None,
    record_count: int | None = None,
) -> None:
    """
    Create a validation result record.
    """

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO validation_results (
                validation_id,
                artifact_id,
                validation_status,
                validation_errors,
                record_count
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                validation_id,
                artifact_id,
                validation_status,
                validation_errors,
                record_count,
            ),
        )

    conn.commit()