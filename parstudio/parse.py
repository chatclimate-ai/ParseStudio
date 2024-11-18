from .parsers.docling_parser import DoclingPDFParser
from .parsers.llama_parser import LlamaPDFParser
from .parsers.pymupdf_parser import PyMuPDFParser
from typing import Literal, List, Union
from .parsers.schema import ParserOutput


class PDFParser:
    def __init__(self, parser: Literal["docling", "llama", "pymupdf"] = "docling"):
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
        Run the PDF parser on the given PDF file.
        """

        outputs = self.parser.parse_and_export(pdf_path, **kwargs)

        return outputs
