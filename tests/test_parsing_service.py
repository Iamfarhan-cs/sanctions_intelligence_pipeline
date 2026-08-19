import os
import uuid

import pytest
from dotenv import load_dotenv

from sanctions_pipeline.parsing.service import parse_minio_artifact
from sanctions_pipeline.storage.minio_client import (
    create_minio_client,
    upload_file,
)


load_dotenv()


@pytest.fixture
def minio_client():
    return create_minio_client(
        endpoint=os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
    )


def test_parse_minio_json_artifact(minio_client, tmp_path):
    bucket = os.environ["MINIO_BUCKET"]
    object_name = f"task-9/{uuid.uuid4()}/sanctions.json"

    artifact = tmp_path / "sanctions.json"

    artifact.write_text(
        '{"name": "Example", "country": "US"}',
        encoding="utf-8",
    )

    upload_file(
        minio_client,
        str(artifact),
        bucket,
        object_name,
    )

    try:
        result = parse_minio_artifact(
            minio_client,
            bucket_name=bucket,
            object_name=object_name,
            file_format="json",
            artifact_id="artifact-minio-001",
            run_id="run-minio-001",
            source_id="source-minio-001",
        )

        assert result.artifact_id == "artifact-minio-001"
        assert result.run_id == "run-minio-001"
        assert result.source_id == "source-minio-001"
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
