from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParsedRecord:
    """
    A single record produced by parsing a validated source artifact.
    """

    record_index: int
    data: dict[str, Any]


@dataclass(frozen=True)
class ParsedArtifact:
    """
    Structured representation of a parsed source artifact.

    The original raw artifact remains unchanged in MinIO.
    """

    artifact_id: str
    run_id: str
    source_id: str
    file_format: str
    records: tuple[ParsedRecord, ...]