from minio import Minio

from sanctions_pipeline.metadata.postgres import (
    get_artifact_with_latest_validation,
)
from sanctions_pipeline.parsing.models import ParsedArtifact
from sanctions_pipeline.parsing.parser import ParserError
from sanctions_pipeline.parsing.service import parse_minio_artifact


def parse_validated_artifact(
    conn,
    minio_client: Minio,
    *,
    artifact_id: str,
    source_id: str,
) -> ParsedArtifact:
    """
    Parse an artifact only when its latest validation result is VALID.
    """

    artifact = get_artifact_with_latest_validation(
        conn,
        artifact_id,
    )

    if artifact is None:
        raise ParserError(
            f"Artifact not found: {artifact_id}"
        )

    validation_status = artifact["validation_status"]

    if validation_status != "VALID":
        raise ParserError(
            f"Artifact is not eligible for parsing: "
            f"{artifact_id} "
            f"(validation status: {validation_status})"
        )

    return parse_minio_artifact(
        minio_client,
        bucket_name=artifact["storage_bucket"],
        object_name=artifact["storage_key"],
        file_format=artifact["file_format"],
        artifact_id=artifact["artifact_id"],
        run_id=artifact["run_id"],
        source_id=source_id,
    )
