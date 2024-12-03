import fitz  # PyMuPDF
from PIL import Image
from typing import Union, List, Generator, Dict
from io import BytesIO
from .schemas import ParserOutput, TableElement, ImageElement, TextElement, Metadata
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
        Load the documents from the given paths.

        Args:
            paths (List[str]): List of paths to the PDF files.
        
        Returns:
            result (Generator[List[Page], None, None]): A generator that yields a list of pages for each document
        """
        for path in paths:
            with fitz.open(path) as doc:
                pages = [doc.load_page(page_num) for page_num in range(doc.page_count)]
                yield pages

    def _validate_modalities(self, modalities: List[str]) -> None:
        """
        Validate the modalities provided by the user. The valid modalities are: ["text", "tables", "images"]

        Args:
            modalities (List[str]): List of modalities to validate

        Raises:
            ValueError: If the modality is not valid
        """
        valid_modalities = ["text", "tables", "images"]
        for modality in modalities:
            if modality not in valid_modalities:
                raise ValueError(
                    f"Invalid modality: {modality}. The valid modalities are: {valid_modalities}"
                )

    def parse(
        self,
        paths: Union[str, List[str]],
        modalities: List[str] = ["text", "tables", "images"],
    ) -> List[ParserOutput]:
        """
        Parse the PDF file and return the extracted the specified modalities.

        Args:
            paths (Union[str, List[str]]): A path or a list of paths to the PDF files.
            modalities (List[str], optional): List of modalities to extract. Defaults to ["text", "tables", "images"].
        
        Returns:
            data (List[ParserOutput]): A list of ParserOutput objects containing the extracted modalities.
        
        Raises:
            ValueError: If the modality is not valid
        
        Example:
        !!! example
            ```python
            parser = PyMuPDFParser()
            data = parser.parse("path/to/file.pdf", modalities=["text", "tables", "images"])
            print(len(data)) 
            # Output: 1
            text = data[0].text # TextElement
            tables = data[0].tables # List of TableElement
            images = data[0].images # List of ImageElement

            # Access the text
            text = text.text


            # Access the first table
            table = tables[0]
            # Access the markdown representation of the table
            table_md = table.markdown
            # Access the dataframe representation of the table
            table_df = table.dataframe
            # Access the metadata of the table
            page_number = table.metadata.page_number
            bbox = table.metadata.bbox

            # Access the first image
            image = images[0]
            # Access the image object
            image_obj = image.image # PIL Image object
            # Access the metadata of the image
            page_number = image.metadata.page_number
            bbox = image.metadata.bbox 
            ```
        """
        self._validate_modalities(modalities)

        if isinstance(paths, str):
            paths = [paths]

        data = []
        for result in self.load_documents(paths):
            output = self.__export_result(result, modalities)

            data.append(output)

        return data

    def __export_result(self, pages: List[Page], modalities: List[str]) -> ParserOutput:
        """
        Export the result of the parsing process.

        Args:
            pages (List[Page]): List of pages
            modalities (List[str]): List of modalities to extract
        
        Returns:
            output (ParserOutput): The ParserOutput object containing the extracted modalities.
        """
        text = TextElement(text="")
        tables: List[TableElement] = []
        images: List[ImageElement] = []

        for page in pages:
            if "text" in modalities:
                text.text += self._extract_text(page).text + "\n"

            if "tables" in modalities:
                tables += self._extract_tables(page)

            if "images" in modalities:
                images += self._extract_images(page)

        return ParserOutput(text=text, tables=tables, images=images)

    @staticmethod
    def _extract_text(page: Page) -> TextElement:
        """
        Extract the text from the page.

        Args:
            page (Page): The page object

        Returns:
            text (TextElement): The extracted text element
        
        Example:
        !!! example
            ```python
            parser = PyMuPDFParser()
            with fitz.open("path/to/file.pdf") as doc:
                page = doc.load_page(0)
                text = parser._extract_text(page)
                print(text.text)
            
            # Output: 'Hello, World!'
            ```
        """
        return TextElement(text=page.get_text("text"))

    @staticmethod
    def _extract_images(page: Page) -> List[ImageElement]:
        """
        Extract the images from the page.

        Args:
            page (Page): The page object

        Returns:
            images (List[ImageElement]): List of ImageElement objects

        Example:
        !!! example
            ```python
            parser = PyMuPDFParser()
            with fitz.open("path/to/file.pdf") as doc:
                page = doc.load_page(0)
                images = parser._extract_images(page)
                image = images[0]
                image_obj = image.image
                page_number = image.metadata.page_number
                bbox = image.metadata.bbox
            ```
        """
        images: List[ImageElement] = []
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = page.parent.extract_image(xref)
            img_data = BytesIO(base_image["image"])
            image = Image.open(img_data).convert("RGB")
            images.append(ImageElement(image=image, metadata=Metadata(page_number=page.number + 1)))
        return images

    @staticmethod
    def _extract_tables(page: Page) -> List[TableElement]:
        """
        Extract the tables from the page.

        Args:
            page (Page): The page object

        Returns:
            tables (List[TableElement]): List of TableElement objects

        Example:
        !!! example
            ```python
            parser = PyMuPDFParser()
            with fitz.open("path/to/file.pdf") as doc:
                page = doc.load_page(0)
                tables = parser._extract_tables(page)
                table = tables[0]
                table_md = table.markdown
                table_df = table.dataframe
                page_number = table.metadata.page_number
                bbox = table.metadata.bbox
            ```
        """
        tabs = page.find_tables()

        tables: List[TableElement] = []
        for tab in tabs:
            tables.append(
                TableElement(
                    markdown=tab.to_markdown(),
                    dataframe=tab.to_pandas(),
                    metadata=Metadata(page_number=page.number + 1),
                )
            )

        return tables

