from abc import ABC, abstractmethod
from pathlib import Path

from sanctions_pipeline.parsing.models import ParsedArtifact


class ParserError(ValueError):
    """
    Raised when a validated artifact cannot be parsed.
    """


class ArtifactParser(ABC):
    """
    Common contract for all source artifact parsers.
    """

    file_format: str

    @abstractmethod
    def parse(
        self,
        file_path: str | Path,
        *,
        artifact_id: str,
        run_id: str,
        source_id: str,
    ) -> ParsedArtifact:
        """
        Parse an already validated artifact.

        The parser must not modify the original artifact.
        """
        raise NotImplementedError
