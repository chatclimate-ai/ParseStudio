from .parsers.docling_parser import DoclingPDFParser
from .parsers.llama_parser import LlamaPDFParser
from .parsers.pymupdf_parser import PyMuPDFParser
from typing import Literal, List, Union
from .parsers.schema import ParserOutput


class PDFParser:
    """
    A class to parse PDF files using different parsers.
    """
    def __init__(self, parser: Literal["docling", "llama", "pymupdf"] = "docling"):
        """
        Initialize the PDF parser with the specified parser.

        Args:
            parser (str): The parser to use. Options are 'docling' and 'llama', and 'pymupdf'. Defaults to 'docling'.

        Raises:
            ValueError: If an invalid parser is specified.
        """
        if parser == "docling":
            self.parser = DoclingPDFParser()
        elif parser == "llama":
            self.parser = LlamaPDFParser()
        elif parser == "pymupdf":
            self.parser = PyMuPDFParser()
        else:
            raise ValueError(
                "Invalid parser specified. Please use 'docling' or 'llama'."
            )

    def run(self, pdf_path: Union[str, List[str]], **kwargs) -> List[ParserOutput]:
        """
        Run the PDF parser on the given PDF file(s).

        Args:
            pdf_path (str or List[str]): The path to the PDF file(s) to parse.
            **kwargs: Additional keyword arguments to pass to the parser.
        
        Returns:
            List[ParserOutput]: The parsed output(s) from the PDF file(s).
        
        Examples:
            >>> parser = PDFParser(parser="docling")
            >>> outputs = parser.run("path/to/file.pdf", backend="docling")
        """

        outputs = self.parser.parse_and_export(pdf_path, **kwargs)

        return outputs
