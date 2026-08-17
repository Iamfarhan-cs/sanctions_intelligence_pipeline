from pathlib import Path
import json
import csv
import xml.etree.ElementTree as ET

from sanctions_pipeline.acquisition.checksum import calculate_sha256


def validate_file_exists_and_not_empty(file_path: str) -> tuple[bool, list[str]]:
    """
    Validate that an artifact exists and contains data.

    Args:
        file_path: Path to the raw artifact.

    Returns:
        Tuple containing:
            - True if the artifact exists and is non-empty.
            - List of validation errors.
    """

    path = Path(file_path)
    errors: list[str] = []

    if not path.exists():
        errors.append("Artifact does not exist.")
        return False, errors

    if not path.is_file():
        errors.append("Artifact path is not a file.")
        return False, errors

    if path.stat().st_size == 0:
        errors.append("Artifact is empty.")
        return False, errors

    return True, errors


def validate_checksum(
    file_path: str,
    expected_checksum: str,
) -> tuple[bool, list[str]]:
    """
    Validate an artifact against its expected SHA-256 checksum.

    Args:
        file_path: Path to the artifact.
        expected_checksum: Expected SHA-256 checksum.

    Returns:
        Tuple containing:
            - True if the checksum matches.
            - List of validation errors.
    """

    actual_checksum = calculate_sha256(file_path)

    if actual_checksum != expected_checksum:
        return False, [
            f"Checksum mismatch. Expected {expected_checksum}, "
            f"got {actual_checksum}."
        ]

    return True, []


def detect_file_format(file_path: str) -> str | None:
    """
    Detect the supported file format from the artifact extension.

    Args:
        file_path: Path to the artifact.

    Returns:
        "xml", "json", or "csv" for supported formats.
        None for unsupported formats.
    """

    suffix = Path(file_path).suffix.lower()

    format_mapping = {
        ".xml": "xml",
        ".json": "json",
        ".csv": "csv",
    }

    return format_mapping.get(suffix)


def validate_xml_structure(file_path: str) -> tuple[bool, list[str]]:
    """
    Validate that an artifact contains well-formed XML.

    Args:
        file_path: Path to the XML artifact.

    Returns:
        Tuple containing:
            - True if the XML is well-formed.
            - List of validation errors.
    """

    try:
        ET.parse(file_path)
    except ET.ParseError as error:
        return False, [f"Invalid XML structure: {error}"]

    return True, []


def validate_json_structure(file_path: str) -> tuple[bool, list[str]]:
    """
    Validate that an artifact contains valid JSON.

    Args:
        file_path: Path to the JSON artifact.

    Returns:
        Tuple containing:
            - True if the JSON is valid.
            - List of validation errors.
    """

    try:
        with Path(file_path).open("r", encoding="utf-8") as file:
            json.load(file)
    except json.JSONDecodeError as error:
        return False, [f"Invalid JSON structure: {error}"]

    return True, []


def validate_csv_structure(file_path: str) -> tuple[bool, list[str]]:
    """
    Validate that an artifact can be read as CSV.

    Args:
        file_path: Path to the CSV artifact.

    Returns:
        Tuple containing:
            - True if the CSV can be read successfully.
            - List of validation errors.
    """

    try:
        with Path(file_path).open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            reader = csv.reader(file, strict=True)

            for _ in reader:
                pass

    except csv.Error as error:
        return False, [f"Invalid CSV structure: {error}"]

    return True, []

STRUCTURE_VALIDATORS = {
    "xml": validate_xml_structure,
    "json": validate_json_structure,
    "csv": validate_csv_structure,
}


def validate_artifact(
    file_path: str,
    expected_checksum: str,
) -> tuple[bool, list[str]]:
    """
    Run all applicable raw artifact validation checks.

    Args:
        file_path: Path to the raw artifact.
        expected_checksum: Expected SHA-256 checksum.

    Returns:
        Tuple containing:
            - True if all validation checks pass.
            - List of validation errors.
    """

    is_valid, errors = validate_file_exists_and_not_empty(file_path)

    if not is_valid:
        return False, errors

    is_valid, errors = validate_checksum(
        file_path,
        expected_checksum,
    )

    if not is_valid:
        return False, errors

    file_format = detect_file_format(file_path)

    if file_format is None:
        return False, ["Unsupported artifact file format."]

    structure_validator = STRUCTURE_VALIDATORS[file_format]

    is_valid, errors = structure_validator(file_path)

    if not is_valid:
        return False, errors

    return True, []