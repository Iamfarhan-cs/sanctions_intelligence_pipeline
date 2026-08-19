import tempfile
from pathlib import Path

from minio import Minio

from sanctions_pipeline.parsing.dispatcher import get_parser
from sanctions_pipeline.parsing.models import ParsedArtifact
from sanctions_pipeline.parsing.parser import ParserError
from sanctions_pipeline.storage.minio_client import read_object


def parse_minio_artifact(
    client: Minio,
    *,
    bucket_name: str,
    object_name: str,
    file_format: str,
    artifact_id: str,
    run_id: str,
    source_id: str,
) -> ParsedArtifact:
    """
    Read a validated raw artifact from MinIO and parse it.

    The raw object in MinIO is never modified.
    """

    parser = get_parser(file_format)

    try:
        raw_bytes = read_object(
            client,
            bucket_name,
            object_name,
        )
    except Exception as error:
        raise ParserError(
            f"Unable to read artifact from MinIO: {error}"
        ) from error

    if not raw_bytes:
        raise ParserError(
            f"MinIO artifact is empty: {bucket_name}/{object_name}"
        )

    suffix = f".{file_format.lower()}"

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory) / f"artifact{suffix}"

        temporary_path.write_bytes(raw_bytes)

        return parser.parse(
            temporary_path,
            artifact_id=artifact_id,
            run_id=run_id,
            source_id=source_id,
        )
