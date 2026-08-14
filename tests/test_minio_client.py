import os

from dotenv import load_dotenv

from sanctions_pipeline.storage.minio_client import (
    create_minio_client,
    upload_file,
)

load_dotenv()


def test_upload_file_to_minio(tmp_path):
    test_file = tmp_path / "minio-test-env.txt"
    test_file.write_text("Task 6 MinIO environment test")

    client = create_minio_client(
        endpoint=os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
    )

    bucket_name = os.environ["MINIO_BUCKET"]
    object_name = "task-6/test/minio-test-env.txt"

    upload_file(
        client=client,
        file_path=str(test_file),
        bucket_name=bucket_name,
        object_name=object_name,
    )

    response = client.stat_object(
        bucket_name,
        object_name,
    )

    assert response.size == test_file.stat().st_size