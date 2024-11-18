from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    EasyOcrOptions,
    TableFormerMode,
    TesseractOcrOptions,
)
from docling.datamodel.document import ConversionResult
from docling.datamodel.base_models import InputFormat, ConversionStatus
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling_core.types.doc import PictureItem, TableItem, ImageRefMode, DoclingDocument
import pandas as pd
from PIL import Image
from typing import Union, List, Generator, Dict
from .schema import ParserOutput
import sys


class DoclingPDFParser:
    """
    Parse a PDF file using the Docling Parser
    """

    def __init__(self):
        self.embed_images = None
        self.initialized = False

    def __initialize_docling(
        self,
        pipeline_options: PdfPipelineOptions,
        backend: Union[DoclingParseDocumentBackend, PyPdfiumDocumentBackend],
    ) -> None:
        """
        Initialize the DocumentConverter with the given pipeline options and backend.

        :param pipeline_options: PdfPipelineOptions
            The pipeline options to use for parsing the document
        :param backend: Union[DoclingParseDocumentBackend, PyPdfiumDocumentBackend]
            The backend to use for parsing the document
        """
        self.converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options, backend=backend
                )
            },
        )

        self.initialized = True

    def load_documents(
        self, paths: List[str], **kwargs
    ) -> Generator[ConversionResult, None, None]:
        """
        Parse the given document and return the parsed result.

        :param paths: List[str]
            The list of paths to the documents to parse
        :param raises_on_error: bool
            Whether to raise an error if the document fails to parse
        :param max_num_pages: int
            The maximum number of pages to parse
        :param max_file_size: int
            The maximum file size to parse
        :return: Generator[ConversionResult, None, None]
            A generator that yields the parsed result for each document

        :raises ValueError: If the Docling Parser has not been initialized
        :raises ValueError: If the document fails to parse
        
        :example:
        >>> parser = DoclingPDFParser()
        >>> for result in parser.load_documents(["path/to/file.pdf"]):
        >>>     if result.status == ConversionStatus.SUCCESS:
        >>>         print(result.document)
        """
        if not self.initialized:
            raise ValueError("The Docling Parser has not been initialized.")

        raises_on_error = kwargs.get("raises_on_error", True)
        max_num_pages = kwargs.get("max_num_pages", sys.maxsize)
        max_file_size = kwargs.get("max_file_size", sys.maxsize)

        yield from self.converter.convert_all(
            paths,
            raises_on_error=raises_on_error,
            max_num_pages=max_num_pages,
            max_file_size=max_file_size,
        )

    def parse_and_export(
        self,
        paths: Union[str, List[str]],
        modalities: List[str] = ["text", "tables", "images"],
        **kwargs,
    ) -> List[ParserOutput]:
        """
        Parse the given document and export the parsed results.
        
        :param paths: Union[str, List[str]]
            The path to the document or a list of paths to the documents to parse
        :param modalities: List[str]
            The modalities to export the parsed results in (text, tables, images)
        :param do_ocr: bool
            Whether to perform OCR on the document
        :param ocr_options: str
            The OCR options to use (easyocr, tesseract)
        :param do_table_structure: bool
            Whether to extract table structure from the document
        :param do_cell_matching: bool
            Whether to perform cell matching on the extracted tables
        :param tableformer_mode: str
            The mode to use for table extraction (ACCURATE, FAST)
        :param images_scale: float
            The scale factor to resize the images by
        :param generate_page_images: bool
            Whether to generate images for each page of the document
        :param generate_picture_images: bool
            Whether to generate images for each picture in the document
        :param generate_table_images: bool
            Whether to generate images for each table in the document
        :param backend: str
            The backend to use for parsing the document (docling, pypdfium)
        :param embed_images: bool
            Whether to embed images in the exported markdown text
        
        :return: List[ParserOutput]
            A list of parsed results for each document
        
        :raises ValueError: If the Docling Parser has not been initialized
        
        :example:
        >>> parser = DoclingPDFParser()
        >>> data = parser.parse_and_export("path/to/file.pdf", modalities=["text", "tables", "images"])

        :example:
        >>> parser = DoclingPDFParser()
        >>> data = parser.parse_and_export(["path/to/file1.pdf", "path/to/file2.pdf"], modalities=["text", "tables", "images"])
        """
        if isinstance(paths, str):
            paths = [paths]

        if not self.initialized:
            # Set pipeline options
            pipeline_options = PdfPipelineOptions()

            # Set ocr options
            pipeline_options.do_ocr = kwargs.get("do_ocr", True)
            ocr_options = kwargs.get("ocr_options", "easyocr")
            if ocr_options == "easyocr":
                pipeline_options.ocr_options = EasyOcrOptions(
                    use_gpu=False,
                    lang=["en"],
                    # force_full_page_ocr=True,
                )
            elif ocr_options == "tesseract":
                pipeline_options.ocr_options = TesseractOcrOptions(
                    lang="eng",
                    # force_full_page_ocr=True,
                )
            else:
                raise ValueError(f"Invalid OCR options specified: {ocr_options}")

            # Set table structure options
            pipeline_options.do_table_structure = kwargs.get("do_table_structure", True)
            pipeline_options.table_structure_options.do_cell_matching = kwargs.get(
                "do_cell_matching", False
            )
            mode = kwargs.get("tableformer_mode", "ACCURATE")
            if mode == "ACCURATE":
                pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
            elif mode == "FAST":
                pipeline_options.table_structure_options.mode = TableFormerMode.FAST
            else:
                raise ValueError(f"Invalid mode specified: {mode}")

            # Set image options
            pipeline_options.images_scale = kwargs.get("images_scale", 1.0)
            pipeline_options.generate_page_images = kwargs.get(
                "generate_page_images", False
            )
            pipeline_options.generate_picture_images = kwargs.get(
                "generate_picture_images", True
            )
            pipeline_options.generate_table_images = kwargs.get(
                "generate_table_images", True
            )

            # Set backend
            backend = kwargs.get("backend", "docling")
            if backend == "docling":
                backend = DoclingParseDocumentBackend
            elif backend == "pypdfium":
                backend = PyPdfiumDocumentBackend
            else:
                raise ValueError(f"Invalid backend specified: {backend}")

            self.embed_images = kwargs.get("embed_images", True)

            # Initialize the Docling Parser
            self.__initialize_docling(pipeline_options, backend)

        data = []
        for result in self.load_documents(paths, **kwargs):
            if result.status == ConversionStatus.SUCCESS:
                output = self.__export_result(result.document, modalities)

                data.append(output)

            else:
                raise ValueError(f"Failed to parse the document: {result.errors}")
        return data

    def __export_result(
        self, document: DoclingDocument, modalities: List[str]
    ) -> ParserOutput:
        """
        Export the parsed results to the output directory.

        :param document: DoclingDocument
            The parsed document to export
        :param modalities: List[str]
            The modalities to export the parsed results in (text, tables, images)

        :return: ParserOutput
            The parsed results for the document
        """
        text = ""
        tables: List[Dict] = []
        images: List[Dict] = []

        if "text" in modalities:
            text = self._extract_text(document)

        if any(modality in modalities for modality in ["tables", "images"]):
            for item, _ in document.iterate_items():
                if "tables" in modalities and isinstance(item, TableItem):
                    tables += self._extract_tables(item)

                if "images" in modalities and isinstance(item, PictureItem):
                    images += self._extract_images(item)

        return ParserOutput(text=text, tables=tables, images=images)

    @staticmethod
    def _extract_tables(item: TableItem) -> List[Dict]:
        """
        Extract tables from the document and return as a list of dictionaries with table markdown, dataframe, and caption data.

        :param item: TableItem
            The table item to extract
        
        :return: List[Dict]
            A list of dictionaries with table markdown and dataframe
        """
        table_md: str = item.export_to_markdown()
        table_df: pd.DataFrame = item.export_to_dataframe()

        return [{"table_md": table_md, "table_df": table_df}]

    @staticmethod
    def _extract_images(item: PictureItem) -> List[Dict]:
        """
        Extract images from the document and return as a list of dictionaries with image and caption data.

        :param item: PictureItem
            The picture item to extract
        
        :return: List[Dict]
            A list of dictionaries with image data
        """
        image: Image.Image = item.image.pil_image
        return [{"image": image}]

    def _extract_text(self, item: DoclingDocument) -> str:
        """
        Extract text from the document.

        :param item: DoclingDocument
            The document to extract text from
        
        :return: str
            The extracted text
        """
        if self.embed_images:
            return item.export_to_markdown(
                image_mode=ImageRefMode.EMBEDDED,
            )

        return item.export_to_markdown(
            image_mode=ImageRefMode.PLACEHOLDER,
        )
