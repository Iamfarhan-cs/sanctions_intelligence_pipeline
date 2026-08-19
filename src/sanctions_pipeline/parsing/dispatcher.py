from sanctions_pipeline.parsing.csv_parser import CsvParser
from sanctions_pipeline.parsing.json_parser import JsonParser
from sanctions_pipeline.parsing.parser import ArtifactParser, ParserError
from sanctions_pipeline.parsing.xml_parser import XmlParser


PARSERS: dict[str, type[ArtifactParser]] = {
    "json": JsonParser,
    "csv": CsvParser,
    "xml": XmlParser,
}


def get_parser(file_format: str) -> ArtifactParser:
    """
    Return the parser for a supported artifact format.

    Args:
        file_format: Validated artifact format.

    Returns:
        An instance of the appropriate parser.

    Raises:
        ParserError: If the format is unsupported.
    """

    normalized_format = file_format.lower()

    parser_class = PARSERS.get(normalized_format)

    if parser_class is None:
        raise ParserError(
            f"Unsupported artifact format for parsing: {file_format}"
        )

    return parser_class()
