from .parsers.docling_parser import DoclingPDFParser
from .parsers.llama_parser import LlamaPDFParser
from .parsers.pymupdf_parser import PyMuPDFParser
from typing import Literal, List, Union, Dict, Type
from .parsers.schemas import ParserOutput


class PDFParser:
    """
    Parse PDF files using different parsers.
    """

    PARSER_MAP: Dict[str, Type] = {
        "docling": DoclingPDFParser,
        "llama": LlamaPDFParser,
        "pymupdf": PyMuPDFParser
    }
    def __init__(
            self, 
            parser: Literal["docling", "llama", "pymupdf"] = "docling", 
            parser_kwargs: dict = {}
            ):
        """
        Initialize the PDF parser with the specified backend.

        Args:
            parser (str): The parser backend to use. Options are 'docling' and 'llama', and 'pymupdf'. Defaults to 'docling'.
            parser_kwargs (dict): Additional keyword arguments to pass to the parser. Check the documentation of the parser for more information.

        Raises:
            ValueError: If an invalid parser is specified.
        """
        parser = parser.lower()
        parser_class = self.PARSER_MAP.get(parser)
        if not parser_class:
            raise ValueError(
                f"Invalid parser: '{parser}'. Valid options are: {list(self.PARSER_MAP.keys())}"
            )
        self.parser = parser_class(**parser_kwargs)

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
            **kwargs: Additional keyword arguments to pass to 'docling' parser. Check the documentation of the parser for more information.
        
        Returns:
            The parsed output(s) from the PDF file(s).
        
        Examples:

        !!! example
            ```python
            from parsestudio.parse import PDFParser
            
            # Initialize the parser
            parser = PDFParser(parser="docling")

            # Parse the PDF file
            outputs = parser.run("path/to/file.pdf")
            print(len(outputs))  # Number of PDF files
            # Output: 1

            # Access text content
            print(outputs[0].text)
            # Output: text='Hello, World!'

            # Access tables
            print(outputs[0].tables)
            # Output:
            # [
            #     TableElement(
            #         markdown='| Column 1 | Column 2 |
            #                   |----------|----------|
            #                   | Value 1  | Value 2  |
            #                   | Value 3  | Value 4  |',
            #         dataframe=  Column 1  Column 2
            #                     0  Value 1  Value 2
            #                     1  Value 3  Value 4,
            #         metadata=Metadata(page_number=1, bbox=[0, 0, 100, 100])
            #     )
            # ]

            for table in outputs[0].tables:
                metadata = table.metadata
                markdown_table = table.markdown
                pandas_dataframe = table.dataframe
                print(metadata)
                print(markdown_table)
            # Output:
            # Metadata(page_number=1, bbox=[0, 0, 100, 100])
            # | Column 1 | Column 2 |
            # |----------|----------|
            # | Value 1  | Value 2  |
            # | Value 3  | Value 4  |

            # Access images
            print(outputs[0].images)
            # Output:
            # [
            #     ImageElement(
            #         image=<PIL.Image.Image image mode=RGB size=233x140 at 0x16E894E50>,
            #         metadata=Metadata(page_number=1, bbox=[0, 0, 100, 100])
            #     )
            # ]

            for image in outputs[0].images:
                metadata = image.metadata
                image = image.image
                print(metadata)
                image.show()
            # Output:
            # Metadata(page_number=1, bbox=[0, 0, 100, 100])
            # [Image shown]
            ```
        """
     

        outputs = self.parser.parse(
            pdf_path, 
            modalities=modalities,
            **kwargs
            )
        return outputs
