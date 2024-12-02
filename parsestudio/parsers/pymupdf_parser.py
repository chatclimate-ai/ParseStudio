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
        """
        for path in paths:
            with fitz.open(path) as doc:
                pages = [doc.load_page(page_num) for page_num in range(doc.page_count)]
                yield pages

    def _validate_modalities(self, modalities: List[str]) -> None:
        """
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
        """
        return TextElement(text=page.get_text("text"))

    @staticmethod
    def _extract_images(page: Page) -> List[ImageElement]:
        """
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

