from pathlib import Path

from minio import Minio


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