from pathlib import Path
from time import sleep

import requests

from sanctions_pipeline.acquisition.checksum import calculate_sha256


def download_file(
    url: str,
    output_path: str,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: int = 2,
) -> tuple[Path, str]:
    """
    Download a file from an HTTP(S) URL with retry handling
    and calculate its SHA-256 checksum.

    Args:
        url: Source URL.
        output_path: Local path where the artifact will be saved.
        timeout: HTTP timeout in seconds.
        max_retries: Maximum number of retries after the initial attempt.
        retry_delay: Seconds to wait between attempts.

    Returns:
        Tuple containing:
            - Path to the downloaded file.
            - SHA-256 checksum.

    Raises:
        requests.RequestException: If all download attempts fail.
    """

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            output.write_bytes(response.content)

            checksum = calculate_sha256(str(output))

            return output, checksum

        except requests.RequestException:
            if attempt == max_retries:
                raise

            sleep(retry_delay)