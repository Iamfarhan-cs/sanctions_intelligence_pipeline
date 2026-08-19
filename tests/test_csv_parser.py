import pytest

from sanctions_pipeline.parsing.csv_parser import CsvParser
from sanctions_pipeline.parsing.parser import ParserError


def test_csv_parser_parses_records(tmp_path):
    artifact = tmp_path / "sanctions.csv"

    artifact.write_text(
        "name,country,type\n"
        "Example One,US,person\n"
        "Example Two,UK,company\n",
        encoding="utf-8",
    )

    result = CsvParser().parse(
        artifact,
        artifact_id="artifact-101",
        run_id="run-101",
        source_id="source-101",
    )

    assert result.artifact_id == "artifact-101"
    assert result.run_id == "run-101"
    assert result.source_id == "source-101"
    assert result.file_format == "csv"

    assert len(result.records) == 2

    assert result.records[0].record_index == 0
    assert result.records[0].data == {
        "name": "Example One",
        "country": "US",
        "type": "person",
    }

    assert result.records[1].record_index == 1
    assert result.records[1].data == {
        "name": "Example Two",
        "country": "UK",
        "type": "company",
    }


def test_csv_parser_preserves_empty_fields(tmp_path):
    artifact = tmp_path / "sanctions.csv"

    artifact.write_text(
        "name,country,type\n"
        "Example,US,\n",
        encoding="utf-8",
    )

    result = CsvParser().parse(
        artifact,
        artifact_id="artifact-102",
        run_id="run-102",
        source_id="source-102",
    )

    assert result.records[0].data == {
        "name": "Example",
        "country": "US",
        "type": "",
    }


def test_csv_parser_rejects_empty_file(tmp_path):
    artifact = tmp_path / "sanctions.csv"
    artifact.touch()

    with pytest.raises(ParserError, match="empty"):
        CsvParser().parse(
            artifact,
            artifact_id="artifact-103",
            run_id="run-103",
            source_id="source-103",
        )


def test_csv_parser_rejects_missing_header(tmp_path):
    artifact = tmp_path / "sanctions.csv"

    artifact.write_text(
        "",
        encoding="utf-8",
    )

    with pytest.raises(ParserError, match="empty"):
        CsvParser().parse(
            artifact,
            artifact_id="artifact-104",
            run_id="run-104",
            source_id="source-104",
        )


def test_csv_parser_rejects_malformed_csv(tmp_path):
    artifact = tmp_path / "sanctions.csv"

    artifact.write_text(
        'name,country\n"Example,US\n',
        encoding="utf-8",
    )

    with pytest.raises(ParserError, match="parse CSV"):
        CsvParser().parse(
            artifact,
            artifact_id="artifact-105",
            run_id="run-105",
            source_id="source-105",
        )
