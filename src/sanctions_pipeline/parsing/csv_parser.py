import csv
from pathlib import Path

from sanctions_pipeline.parsing.models import ParsedArtifact, ParsedRecord
from sanctions_pipeline.parsing.parser import ArtifactParser, ParserError


class CsvParser(ArtifactParser):
    """
    Parser for validated CSV source artifacts.
    """

    file_format = "csv"

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
            with path.open(
                "r",
                encoding="utf-8",
                newline="",
            ) as file:
                reader = csv.DictReader(file, strict=True)

                if reader.fieldnames is None:
                    raise ParserError(
                        "CSV artifact does not contain a header row."
                    )

                records = []

                for index, row in enumerate(reader):
                    records.append(
                        ParsedRecord(
                            record_index=index,
                            data=dict(row),
                        )
                    )

        except UnicodeDecodeError as error:
            raise ParserError(
                f"Unable to decode CSV artifact: {error}"
            ) from error
        except csv.Error as error:
            raise ParserError(
                f"Unable to parse CSV artifact: {error}"
            ) from error

        return ParsedArtifact(
            artifact_id=artifact_id,
            run_id=run_id,
            source_id=source_id,
            file_format=self.file_format,
            records=tuple(records),
        )
