from typing import Any

from .openai_file_search_parser import OpenAIAssistantPDFParser
from .schemas import ParserOutput


class OpenAIPDFParser:
    """
    OpenAI PDF Parser using assistant approach.
    Uses OpenAI's Assistant API with file search capabilities for comprehensive PDF processing.

    Args:
        openai_options: Options to pass to the underlying parser
    """

    def __init__(self, openai_options: dict[str, Any] | None = None):
        self.parser = OpenAIAssistantPDFParser(openai_options)

    def parse(
        self,
        paths: str | list[str],
        modalities: list[str] | None = None,
        **kwargs,
    ) -> list[ParserOutput]:
        """
        Parse PDF files using OpenAI's file search approach.

        Args:
            paths: Path or list of paths to PDF files
            modalities: List of modalities to extract
            **kwargs: Additional arguments passed to the underlying parser

        Returns:
            List of ParserOutput objects
        """
        return self.parser.parse(paths, modalities, **kwargs)

    def load_documents(self, paths: list[str]):
        """Load documents using the file search parser."""
        return self.parser.load_documents(paths)

    def _validate_modalities(self, modalities: list[str]) -> None:
        """Validate modalities using the parser."""
        return self.parser._validate_modalities(modalities)
