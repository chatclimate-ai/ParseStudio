import fitz  # PyMuPDF
from PIL import Image
from typing import Union, List, Generator, Dict
from io import BytesIO
from .schema import ParserOutput
from fitz import Page


class PyMuPDFParser:
    """
    Parse a PDF file using PyMuPDF parser.
    """

    def __init__(self):
        pass

    @staticmethod
    def load_documents(paths: List[str]) -> Generator[List[Page], None, None]:
        """
        Load a list of PDF documents and return a generator of lists of pages.

        Args:
            paths (List[str]): List of paths to PDF files.
        
        Returns:
            documents (Generator[List[Page], None, None]): Generator of lists of pages.
        """
        for path in paths:
            with fitz.open(path) as doc:
                pages = [doc.load_page(page_num) for page_num in range(doc.page_count)]
                yield pages

    def parse_and_export(
        self,
        paths: Union[str, List[str]],
        modalities: List[str] = ["text", "tables", "images"],
    ) -> List[ParserOutput]:
        """
        Parse the given documents and export the parsed results in the specified modalities. The parsed results are exported as a ParserOutput object.

        Args:
            paths (Union[str, List[str]]): The path to the PDF file or a list of paths to the PDF files.
            modalities (List[str]): The list of modalities to export. Default is ["text", "tables", "images"].
        
        Returns:
            data (List[ParserOutput]): A list of ParserOutput objects containing the parsed results.

        Example:
            >>> parser = PyMuPDFParser()
            >>> data = parser.parse_and_export("path/to/pdf/file.pdf", modalities=["text", "tables", "images"])
            >>> print(data)
            ... [ParserOutput(text="...", tables=[...], images=[...])]
        """
        if isinstance(paths, str):
            paths = [paths]

        data = []
        for result in self.load_documents(paths):
            output = self.__export_result(result, modalities)

            data.append(output)

        return data

    def __export_result(self, pages: List[Page], modalities: List[str]) -> ParserOutput:
        """
        Export the parsed results in a ParserOutput object for the given document.

        Args:
            pages (List[Page]): List of pages of the document.
            modalities (List[str]): List of modalities to export.
        
        Returns:
            output (ParserOutput): ParserOutput object containing the parsed results.
        """
        text = ""
        tables: List[Dict] = []
        images: List[Dict] = []

        for page in pages:
            if "text" in modalities:
                text += self._extract_text(page) + "\n"

            if "tables" in modalities:
                tables += self._extract_tables(page)

            if "images" in modalities:
                images += self._extract_images(page)

        return ParserOutput(text=text, tables=tables, images=images)

    @staticmethod
    def _extract_text(page: Page) -> str:
        """
        Extract text from a page.

        Args:
            page (Page): The page object to extract text from.
        
        Returns:
            text (str): The extracted text from the page.
        """
        return page.get_text("text")

    @staticmethod
    def _extract_images(page: Page) -> List[Dict]:
        """
        Extract images from the document and return as a list of dictionaries with image data.

        Args:
            page (Page): The page object to extract images from.
        
        Returns:
            images (List[Dict]): A list of dictionaries containing image data.
            Each dictionary contains the image data as a PIL Image object.
        """
        images = []
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = page.parent.extract_image(xref)
            img_data = BytesIO(base_image["image"])
            image = Image.open(img_data).convert("RGB")
            images.append({"image": image})
        return images

    @staticmethod
    def _extract_tables(page: Page) -> List[Dict]:
        """
        Extract tables from the document and return as a list of dictionaries with table markdown and dataframe data.

        Args:
            page (Page): The page object to extract tables from.
        
        Returns:
            tables (List[Dict]): A list of dictionaries with table data.
            Each dictionary contains a markdown table (table_md) and a pandas dataframe (table_df).
        """

        tabs = page.find_tables()

        tables = []
        for tab in tabs:
            tables.append({"table_md": tab.to_markdown(), "table_df": tab.to_pandas()})

        return tables
