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

        Args:
            pipeline_options (PdfPipelineOptions): The pipeline options to use for parsing the document
            backend (Union[DoclingParseDocumentBackend, PyPdfiumDocumentBackend]): The backend to use for parsing the document
        
        Returns:
            None
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
        Load the given documents and parse them. The documents are parsed in parallel.

        Args:
            paths (List[str]): The list of paths to the documents to parse
            raises_on_error (bool): Whether to raise an error if the document fails to parse. Default is True
            max_num_pages (int): The maximum number of pages to parse. If the document has more pages, it will be skipped. Default is sys.maxsize
            max_file_size (int): The maximum file size to parse. If the document is larger, it will be skipped. Default is sys.maxsize
        
        Returns:
            conversion_result (Generator[ConversionResult, None, None]): A generator that yields the parsed result for each document (file)

        Raises:
            ValueError: If the Docling Parser has not been initialized
        
        Example:
            >>> parser = DoclingPDFParser()
            >>> for result in parser.load_documents(["path/to/file1.pdf", "path/to/file2.pdf"]):
            ...     if result.status == ConversionStatus.SUCCESS:
            ...         print(result.document)
            ...     else:
            ...         print(result.errors)

            ... ConversionResult(status=<ConversionStatus.SUCCESS: 'SUCCESS'>, document=<DoclingDocument>, errors=None)
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
        Parse the given documents and export the parsed results in the specified modalities. The parsed results are exported as a ParserOutput object.

        Args:
            paths (Union[str, List[str]): The path(s) to the document(s) to parse
            modalities (List[str]): The modalities to export the parsed results in (text, tables, images). Default is ["text", "tables", "images"]
            do_ocr (bool): Whether to perform OCR on the document. Default is True.
            ocr_options (str): The OCR options to use (easyocr, tesseract). Default is easyocr.
            do_table_structure (bool): Whether to extract table structure from the document. Default is True.
            do_cell_matching (bool): Whether to perform cell matching on the tables. Default is False.
            tableformer_mode (str): The mode to use for extracting table structure (ACCURATE, FAST). Default is ACCURATE.
            images_scale (float): The scale factor to apply to the images. Default is 1.0.
            generate_page_images (bool): Whether to generate images for each page. Default is False.
            generate_picture_images (bool): Whether to generate images for pictures. Default is True.
            generate_table_images (bool): Whether to generate images for tables. Default is True.
            backend (str): The backend to use for parsing the document (docling, pypdfium). Default is docling.
            embed_images (bool): Whether to embed images in the exported text (markdown string). Default is True.

        Returns:
            data (List[ParserOutput]): A list of parsed results for the document(s)

        Raises:
            ValueError: If the OCR options specified are invalid
            ValueError: If the mode specified for the tableformer is invalid
            ValueError: If the backend specified is invalid
        
        Example:
            >>> parser = DoclingPDFParser()
            >>> data = parser.parse_and_export("path/to/file.pdf", modalities=["text", "tables", "images"])
            >>> print(data)
            ... [ParserOutput(text="...", tables=[{"table_md": "...", "table_df": pd.DataFrame}], images=[{"image": Image.Image}])]
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
        Export the parsed results in a ParserOutput object for the given document.

        Args:
            document (DoclingDocument): The document to export
            modalities (List[str]): The modalities to export the parsed results in (text, tables, images)
        
        Returns:
            output (ParserOutput): The parsed results for the document
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
        Extract tables from the document and return as a list of dictionaries with table markdown and dataframe data.

        Args:
            item (TableItem): The table item to extract
        
        Returns:
            tables (List[Dict]): A list of dictionaries with table data. Each dictionary contains a markdown table (table_md) and a pandas dataframe (table_df).

        Example:
            >>> tables = self._extract_tables(item)
            >>> print(tables)
            ... [{"table_md": "...", "table_df": pd.DataFrame}]
        """
        table_md: str = item.export_to_markdown()
        table_df: pd.DataFrame = item.export_to_dataframe()

        return [{"table_md": table_md, "table_df": table_df}]

    @staticmethod
    def _extract_images(item: PictureItem) -> List[Dict]:
        """
        Extract images from the document and return as a list of dictionaries with image data.

        Args:
            item (PictureItem): The picture item to extract
        
        Returns:
            images (List[Dict]): A list of dictionaries with image data. Each dictionary contains the image data as a PIL Image object.
        """
        image: Image.Image = item.image.pil_image
        return [{"image": image}]

    def _extract_text(self, item: DoclingDocument) -> str:
        """
        Extract text from the document and return as a markdown string.

        Args:
            item (DoclingDocument): The document to extract text from
        
        Returns:
            text (str): The text extracted from the document as a markdown string. If embed_images is True, the images are embedded in the text. Otherwise, the images are replaced with the image placeholder (<!-- image -->).
        """
        if self.embed_images:
            return item.export_to_markdown(
                image_mode=ImageRefMode.EMBEDDED,
            )

        return item.export_to_markdown(
            image_mode=ImageRefMode.PLACEHOLDER,
        )
