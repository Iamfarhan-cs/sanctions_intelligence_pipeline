import pytest

from sanctions_pipeline.parsing.csv_parser import CsvParser
from sanctions_pipeline.parsing.dispatcher import get_parser
from sanctions_pipeline.parsing.json_parser import JsonParser
from sanctions_pipeline.parsing.parser import ParserError
from sanctions_pipeline.parsing.xml_parser import XmlParser


def test_get_parser_returns_json_parser():
    parser = get_parser("json")

    assert isinstance(parser, JsonParser)


def test_get_parser_returns_csv_parser():
    parser = get_parser("csv")

    assert isinstance(parser, CsvParser)


def test_get_parser_returns_xml_parser():
    parser = get_parser("xml")

    assert isinstance(parser, XmlParser)


def test_get_parser_is_case_insensitive():
    assert isinstance(get_parser("JSON"), JsonParser)
    assert isinstance(get_parser("CSV"), CsvParser)
    assert isinstance(get_parser("XML"), XmlParser)


def test_get_parser_rejects_unsupported_format():
    with pytest.raises(
        ParserError,
        match="Unsupported artifact format",
    ):
        get_parser("yaml")
