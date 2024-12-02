from .parsers.docling_parser import DoclingPDFParser
from .parsers.llama_parser import LlamaPDFParser
from .parsers.pymupdf_parser import PyMuPDFParser
from typing import Literal, List, Union
from .parsers.schemas import ParserOutput


class PDFParser:
    """
    A class to parse PDF files using different parsers.
    """
    def __init__(self, parser: Literal["docling", "llama", "pymupdf"] = "docling", **parser_kwargs):
        """
        Initialize the PDF parser with the specified parser.

        Args:
            parser (str): The parser to use. Options are 'docling' and 'llama', and 'pymupdf'. Defaults to 'docling'.
            **parser_kwargs: Additional keyword arguments to pass to the parser. Check the documentation of the parser for more information.

        Raises:
            ValueError: If an invalid parser is specified.
        """
        if parser == "docling":
            self.parser = DoclingPDFParser(**parser_kwargs)
        elif parser == "llama":
            self.parser = LlamaPDFParser(**parser_kwargs)
        elif parser == "pymupdf":
            self.parser = PyMuPDFParser()
        else:
            raise ValueError(
                "Invalid parser specified. Please use 'docling', 'llama', or 'pymupdf'."
            )

    def run(
            self, 
            pdf_path: Union[str, List[str]],
            modalities: List[str] = ["text", "tables", "images"],
            **kwargs
            ) -> List[ParserOutput]:
        """
        Run the PDF parser on the given PDF file(s).

        Args:
            pdf_path (str or List[str]): The path to the PDF file(s) to parse.
            modalities (List[str]): The modalities to extract from the PDF file(s). Defaults to ["text", "tables", "images"].
            **kwargs: Additional keyword arguments to pass to 'docling' parser.
        
        Returns:
            List[ParserOutput]: The parsed output(s) from the PDF file(s).
        
        Examples:
            >>> parser = PDFParser(parser="docling")
            >>> outputs = parser.run("path/to/file.pdf", backend="docling")
            >>> print(len(outputs))
            1
            >>> print(outputs[0].text)
            "This is the extracted text from the PDF file."
            >>> for table in outputs[0].tables:
            ...     metadata = table.metadata
            ...     markdown_table = table.markdown
            ...     pandas_dataframe = table.dataframe
            ...     print(metadata)
            ...     print(markdown_table)
            ...     break
            Metadata(page_number=1, bbox=[0, 0, 100, 100])
            | Column 1 | Column 2 |
            |----------|----------|
            | Value 1  | Value 2  |
            | Value 3  | Value 4  |
        """

        outputs = self.parser.parse(
            pdf_path, 
            modalities=modalities,
            **kwargs
            )
        return outputs
