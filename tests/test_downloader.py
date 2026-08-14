from pathlib import Path
from unittest.mock import Mock, patch

import requests

from sanctions_pipeline.acquisition.downloader import download_file


def test_download_file(tmp_path):
    output_path = tmp_path / "test.txt"

    result_path, checksum = download_file(
        "https://example.com/",
        str(output_path),
    )

    assert isinstance(result_path, Path)
    assert result_path.exists()
    assert result_path.stat().st_size > 0

    assert isinstance(checksum, str)
    assert len(checksum) == 64
    assert checksum == checksum.lower()


def test_download_retries_after_request_failure(tmp_path):
    output_path = tmp_path / "retry-test.txt"

    successful_response = Mock()
    successful_response.raise_for_status.return_value = None
    successful_response.content = b"download successful"

    with patch(
        "sanctions_pipeline.acquisition.downloader.requests.get"
    ) as mock_get:
        mock_get.side_effect = [
            requests.ConnectionError("temporary failure"),
            requests.ConnectionError("temporary failure"),
            successful_response,
        ]

        result_path, checksum = download_file(
            "https://example.com/",
            str(output_path),
            max_retries=2,
            retry_delay=0,
        )

    assert result_path.exists()
    assert result_path.read_bytes() == b"download successful"

    assert isinstance(checksum, str)
    assert len(checksum) == 64
    assert checksum == checksum.lower()

    assert mock_get.call_count == 3


def test_download_raises_after_all_retries_fail(tmp_path):
    output_path = tmp_path / "failed-download.txt"

    with patch(
        "sanctions_pipeline.acquisition.downloader.requests.get"
    ) as mock_get:
        mock_get.side_effect = requests.ConnectionError("connection failed")

        try:
            download_file(
                "https://example.com/",
                str(output_path),
                max_retries=2,
                retry_delay=0,
            )
        except requests.ConnectionError as exc:
            assert str(exc) == "connection failed"
        else:
            raise AssertionError("Expected ConnectionError was not raised")

    assert mock_get.call_count == 3
    assert not output_path.exists()