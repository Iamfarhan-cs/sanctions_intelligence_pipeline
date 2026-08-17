from sanctions_pipeline.acquisition.checksum import calculate_sha256

from sanctions_pipeline.validation.validator import (
    detect_file_format,
    validate_artifact,
    validate_checksum,
    validate_csv_structure,
    validate_file_exists_and_not_empty,
    validate_json_structure,
    validate_xml_structure,
)


def test_validate_existing_non_empty_file(tmp_path):
    artifact = tmp_path / "valid.xml"
    artifact.write_text("<sanctions></sanctions>")

    is_valid, errors = validate_file_exists_and_not_empty(str(artifact))

    assert is_valid is True
    assert errors == []


def test_validate_missing_file(tmp_path):
    artifact = tmp_path / "missing.xml"

    is_valid, errors = validate_file_exists_and_not_empty(str(artifact))

    assert is_valid is False
    assert errors == ["Artifact does not exist."]


def test_validate_empty_file(tmp_path):
    artifact = tmp_path / "empty.xml"
    artifact.touch()

    is_valid, errors = validate_file_exists_and_not_empty(str(artifact))

    assert is_valid is False
    assert errors == ["Artifact is empty."]


def test_validate_matching_checksum(tmp_path):
    artifact = tmp_path / "test.txt"
    artifact.write_bytes(b"hello sanctions pipeline")

    expected_checksum = (
        "c206464f523376ce8c5704a4729330832eabaa8a170d1e8ed9f83814f00196d2"
    )

    is_valid, errors = validate_checksum(
        str(artifact),
        expected_checksum,
    )

    assert is_valid is True
    assert errors == []


def test_validate_mismatched_checksum(tmp_path):
    artifact = tmp_path / "test.txt"
    artifact.write_bytes(b"hello sanctions pipeline")

    expected_checksum = "incorrect-checksum"

    is_valid, errors = validate_checksum(
        str(artifact),
        expected_checksum,
    )

    assert is_valid is False
    assert len(errors) == 1
    assert errors[0].startswith("Checksum mismatch.")


def test_detect_xml_format():
    assert detect_file_format("sanctions.xml") == "xml"


def test_detect_json_format():
    assert detect_file_format("sanctions.json") == "json"


def test_detect_csv_format():
    assert detect_file_format("sanctions.csv") == "csv"


def test_detect_unsupported_format():
    assert detect_file_format("sanctions.txt") is None


def test_detect_format_is_case_insensitive():
    assert detect_file_format("SANCTIONS.XML") == "xml"



def test_validate_valid_xml_structure(tmp_path):
    artifact = tmp_path / "sanctions.xml"
    artifact.write_text(
        "<sanctions><entity>Example</entity></sanctions>"
    )

    is_valid, errors = validate_xml_structure(str(artifact))

    assert is_valid is True
    assert errors == []


def test_validate_invalid_xml_structure(tmp_path):
    artifact = tmp_path / "sanctions.xml"
    artifact.write_text(
        "<sanctions><entity>Example</sanctions>"
    )

    is_valid, errors = validate_xml_structure(str(artifact))

    assert is_valid is False
    assert len(errors) == 1
    assert errors[0].startswith("Invalid XML structure:")


def test_validate_valid_json_structure(tmp_path):
    artifact = tmp_path / "sanctions.json"
    artifact.write_text(
        '{"entities": []}',
        encoding="utf-8",
    )

    is_valid, errors = validate_json_structure(str(artifact))

    assert is_valid is True
    assert errors == []

def test_validate_invalid_json_structure(tmp_path):
    artifact = tmp_path / "sanctions.json"
    artifact.write_text(
        '{"entities": [}',
        encoding="utf-8",
    )

    is_valid, errors = validate_json_structure(str(artifact))

    assert is_valid is False
    assert len(errors) == 1
    assert errors[0].startswith("Invalid JSON structure:")


def test_validate_valid_csv_structure(tmp_path):
    artifact = tmp_path / "sanctions.csv"
    artifact.write_text(
        "name,country\nExample,US\n",
        encoding="utf-8",
    )

    is_valid, errors = validate_csv_structure(str(artifact))

    assert is_valid is True
    assert errors == []


def test_validate_invalid_csv_structure(tmp_path):
    artifact = tmp_path / "sanctions.csv"
    artifact.write_text(
        'name,country\n"Example,US\n',
        encoding="utf-8",
    )

    is_valid, errors = validate_csv_structure(str(artifact))

    assert is_valid is False
    assert len(errors) == 1
    assert errors[0].startswith("Invalid CSV structure:")



def test_validate_artifact_with_valid_xml(tmp_path):
    artifact = tmp_path / "sanctions.xml"
    artifact.write_text(
        "<sanctions><entity>Example</entity></sanctions>",
        encoding="utf-8",
    )

    expected_checksum = calculate_sha256(str(artifact))

    is_valid, errors = validate_artifact(
        str(artifact),
        expected_checksum,
    )

    assert is_valid is True
    assert errors == []


def test_validate_artifact_with_invalid_checksum(tmp_path):
    artifact = tmp_path / "sanctions.xml"
    artifact.write_text(
        "<sanctions><entity>Example</entity></sanctions>",
        encoding="utf-8",
    )

    is_valid, errors = validate_artifact(
        str(artifact),
        "incorrect-checksum",
    )

    assert is_valid is False
    assert len(errors) == 1
    assert errors[0].startswith("Checksum mismatch.")



def test_validate_artifact_with_unsupported_format(tmp_path):
    artifact = tmp_path / "sanctions.txt"
    artifact.write_text(
        "sanctions data",
        encoding="utf-8",
    )

    expected_checksum = calculate_sha256(str(artifact))

    is_valid, errors = validate_artifact(
        str(artifact),
        expected_checksum,
    )

    assert is_valid is False
    assert errors == ["Unsupported artifact file format."]


def test_validate_artifact_with_invalid_xml(tmp_path):
    artifact = tmp_path / "sanctions.xml"
    artifact.write_text(
        "<sanctions><entity>Example</sanctions>",
        encoding="utf-8",
    )

    expected_checksum = calculate_sha256(str(artifact))

    is_valid, errors = validate_artifact(
        str(artifact),
        expected_checksum,
    )

    assert is_valid is False
    assert len(errors) == 1
    assert errors[0].startswith("Invalid XML structure:")