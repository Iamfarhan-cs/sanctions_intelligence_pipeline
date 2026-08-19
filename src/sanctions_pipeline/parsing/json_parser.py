import json
from pathlib import Path
from typing import Any

from sanctions_pipeline.parsing.models import ParsedArtifact, ParsedRecord
from sanctions_pipeline.parsing.parser import ArtifactParser, ParserError


class JsonParser(ArtifactParser):
    """
    Parser for validated JSON source artifacts.
    """

    file_format = "json"

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
            with path.open("r", encoding="utf-8") as file:
                payload: Any = json.load(file)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ParserError(
                f"Unable to parse JSON artifact: {error}"
            ) from error

        if isinstance(payload, dict):
            values = [payload]
        elif isinstance(payload, list):
            values = payload
        else:
            raise ParserError(
                "JSON root must be an object or an array of objects."
            )

        records: list[ParsedRecord] = []

        for index, value in enumerate(values):
            if not isinstance(value, dict):
                raise ParserError(
                    f"JSON record at index {index} must be an object."
                )

            records.append(
                ParsedRecord(
                    record_index=index,
                    data=value,
                )
            )

        return ParsedArtifact(
            artifact_id=artifact_id,
            run_id=run_id,
            source_id=source_id,
            file_format=self.file_format,
            records=tuple(records),
        )
