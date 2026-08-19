import pytest

from sanctions_pipeline.parsing.parser import ParserError
from sanctions_pipeline.parsing.xml_parser import XmlParser


def test_xml_parser_parses_records(tmp_path):
    artifact = tmp_path / "sanctions.xml"

    artifact.write_text(
        """<sanctions>
    <entity id="001">
        <name>Example One</name>
        <country>US</country>
    </entity>
    <entity id="002">
        <name>Example Two</name>
        <country>UK</country>
    </entity>
</sanctions>""",
        encoding="utf-8",
    )

    result = XmlParser().parse(
        artifact,
        artifact_id="artifact-201",
        run_id="run-201",
        source_id="source-201",
    )

    assert result.artifact_id == "artifact-201"
    assert result.run_id == "run-201"
    assert result.source_id == "source-201"
    assert result.file_format == "xml"

    assert len(result.records) == 2

    assert result.records[0].record_index == 0
    assert result.records[0].data == {
        "entity": {
            "@attributes": {"id": "001"},
            "name": "Example One",
            "country": "US",
        }
    }

    assert result.records[1].record_index == 1
    assert result.records[1].data == {
        "entity": {
            "@attributes": {"id": "002"},
            "name": "Example Two",
            "country": "UK",
        }
    }


def test_xml_parser_preserves_repeated_elements(tmp_path):
    artifact = tmp_path / "sanctions.xml"

    artifact.write_text(
        """<sanctions>
    <entity>
        <name>Example</name>
        <alias>A</alias>
        <alias>B</alias>
    </entity>
</sanctions>""",
        encoding="utf-8",
    )

    result = XmlParser().parse(
        artifact,
        artifact_id="artifact-202",
        run_id="run-202",
        source_id="source-202",
    )

    assert result.records[0].data == {
        "entity": {
            "name": "Example",
            "alias": ["A", "B"],
        }
    }


def test_xml_parser_parses_single_root_record(tmp_path):
    artifact = tmp_path / "sanctions.xml"

    artifact.write_text(
        "<entity><name>Example</name></entity>",
        encoding="utf-8",
    )

    result = XmlParser().parse(
        artifact,
        artifact_id="artifact-203",
        run_id="run-203",
        source_id="source-203",
    )

    assert len(result.records) == 1
    assert result.records[0].record_index == 0
    assert result.records[0].data == {
        "name": "Example",
    }


def test_xml_parser_rejects_empty_file(tmp_path):
    artifact = tmp_path / "sanctions.xml"
    artifact.touch()

    with pytest.raises(ParserError, match="empty"):
        XmlParser().parse(
            artifact,
            artifact_id="artifact-204",
            run_id="run-204",
            source_id="source-204",
        )


def test_xml_parser_rejects_malformed_xml(tmp_path):
    artifact = tmp_path / "sanctions.xml"

    artifact.write_text(
        "<sanctions><entity></sanctions>",
        encoding="utf-8",
    )

    with pytest.raises(ParserError, match="parse XML"):
        XmlParser().parse(
            artifact,
            artifact_id="artifact-205",
            run_id="run-205",
            source_id="source-205",
        )