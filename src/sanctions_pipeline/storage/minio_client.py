from pathlib import Path

from minio import Minio
from minio.commonconfig import CopySource


def create_minio_client(
    endpoint: str,
    access_key: str,
    secret_key: str,
) -> Minio:
    """
    Create a MinIO client from an HTTP(S) endpoint.
    """

    secure = endpoint.startswith("https://")

    endpoint = endpoint.replace("http://", "").replace("https://", "")

    return Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure,
    )


def upload_file(
    client: Minio,
    file_path: str,
    bucket_name: str,
    object_name: str,
) -> None:
    """
    Upload a local file to MinIO.
    """

    file = Path(file_path)

    client.fput_object(
        bucket_name,
        object_name,
        str(file),
    )


def copy_object(
    client: Minio,
    source_bucket: str,
    source_object: str,
    destination_bucket: str,
    destination_object: str,
) -> None:
    """
    Copy an existing MinIO object to another bucket/object.
    """

    source = CopySource(
        source_bucket,
        source_object,
    )

    client.copy_object(
        destination_bucket,
        destination_object,
        source,
    )


def stat_object(
    client: Minio,
    bucket_name: str,
    object_name: str,
):
    """
    Retrieve metadata for an existing MinIO object.
    """

    return client.stat_object(
        bucket_name,
        object_name,
    )

def read_object(
    client: Minio,
    bucket_name: str,
    object_name: str,
) -> bytes:
    """
    Read an existing MinIO object into memory.
    """

    response = client.get_object(
        bucket_name,
        object_name,
    )

    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()
