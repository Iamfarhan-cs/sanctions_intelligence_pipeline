from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Any

from sanctions_pipeline.parsing.models import ParsedArtifact, ParsedRecord
from sanctions_pipeline.parsing.parser import ArtifactParser, ParserError


def element_to_data(element: ET.Element) -> Any:
    """
    Convert an XML element into a source-preserving Python structure.
    """

    children = list(element)

    if not children and not element.attrib:
        return element.text or ""

    data: dict[str, Any] = {}

    if element.attrib:
        data["@attributes"] = dict(element.attrib)

    for child in children:
        child_value = element_to_data(child)

        if child.tag not in data:
            data[child.tag] = child_value
        else:
            existing = data[child.tag]

            if isinstance(existing, list):
                existing.append(child_value)
            else:
                data[child.tag] = [existing, child_value]

    if element.text and element.text.strip():
        data["#text"] = element.text.strip()

    return data


class XmlParser(ArtifactParser):
    """
    Parser for validated XML source artifacts.
    """

    file_format = "xml"

    def parse(
        self,
        file_path: str | Path,
        *,
        artifact_id: str,
        run_id: str,
        source_id: str,
    ) -> ParsedArtifact:
        path = Path(file_path)

        if not path.is_file():
            raise ParserError(f"Artifact does not exist: {path}")

        if path.stat().st_size == 0:
            raise ParserError(f"Artifact is empty: {path}")

        try:
            root = ET.parse(path).getroot()
        except (ET.ParseError, OSError, UnicodeDecodeError) as error:
            raise ParserError(
                f"Unable to parse XML artifact: {error}"
            ) from error

        children = list(root)

        if children:
            records = tuple(
                ParsedRecord(
                    record_index=index,
                    data={child.tag: element_to_data(child)},
                )
                for index, child in enumerate(children)
            )
        else:
            records = (
                ParsedRecord(
                    record_index=0,
                    data={root.tag: element_to_data(root)},
                ),
            )

        return ParsedArtifact(
            artifact_id=artifact_id,
            run_id=run_id,
            source_id=source_id,
            file_format=self.file_format,
            records=records,
        )
