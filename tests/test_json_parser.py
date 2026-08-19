import json

import pytest

from sanctions_pipeline.parsing.json_parser import JsonParser
from sanctions_pipeline.parsing.parser import ParserError


def test_json_parser_parses_array(tmp_path):
    artifact = tmp_path / "sanctions.json"

    artifact.write_text(
        json.dumps(
            [
                {"name": "Example One", "country": "US"},
                {"name": "Example Two", "country": "UK"},
            ]
        ),
        encoding="utf-8",
    )

    result = JsonParser().parse(
        artifact,
        artifact_id="artifact-001",
        run_id="run-001",
        source_id="source-001",
    )

    assert result.artifact_id == "artifact-001"
    assert result.run_id == "run-001"
    assert result.source_id == "source-001"
    assert result.file_format == "json"

    assert len(result.records) == 2

    assert result.records[0].record_index == 0
    assert result.records[0].data == {
        "name": "Example One",
        "country": "US",
    }

    assert result.records[1].record_index == 1
    assert result.records[1].data == {
        "name": "Example Two",
        "country": "UK",
    }


def test_json_parser_parses_single_object(tmp_path):
    artifact = tmp_path / "sanctions.json"

    artifact.write_text(
        json.dumps(
            {
                "name": "Example",
                "country": "US",
            }
        ),
        encoding="utf-8",
    )

    result = JsonParser().parse(
        artifact,
        artifact_id="artifact-002",
        run_id="run-002",
        source_id="source-002",
    )

    assert len(result.records) == 1
    assert result.records[0].record_index == 0
    assert result.records[0].data == {
        "name": "Example",
        "country": "US",
    }


def test_json_parser_rejects_scalar_root(tmp_path):
    artifact = tmp_path / "sanctions.json"

    artifact.write_text("123", encoding="utf-8")

    with pytest.raises(
        ParserError,
        match="object or an array",
    ):
        JsonParser().parse(
            artifact,
            artifact_id="artifact-003",
            run_id="run-003",
            source_id="source-003",
        )


def test_json_parser_rejects_non_object_record(tmp_path):
    artifact = tmp_path / "sanctions.json"

    artifact.write_text(
        json.dumps(
            [
                {"name": "Valid"},
                "invalid-record",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ParserError,
        match="record at index 1",
    ):
        JsonParser().parse(
            artifact,
            artifact_id="artifact-004",
            run_id="run-004",
            source_id="source-004",
        )


def test_json_parser_rejects_empty_file(tmp_path):
    artifact = tmp_path / "sanctions.json"
    artifact.touch()

    with pytest.raises(ParserError, match="empty"):
        JsonParser().parse(
            artifact,
            artifact_id="artifact-005",
            run_id="run-005",
            source_id="source-005",
        )
