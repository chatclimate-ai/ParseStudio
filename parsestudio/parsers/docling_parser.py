from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions, TableFormerMode, EasyOcrOptions
from docling.datamodel.document import ConversionResult
from docling.datamodel.base_models import InputFormat, ConversionStatus
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling_core.types.doc import PictureItem, TableItem, DoclingDocument
import pandas as pd
from PIL import Image
from typing import Union, List, Generator, Optional
from .schemas import ParserOutput, TableElement, ImageElement, TextElement, Metadata
import sys



class DoclingPDFParser:
    """
    Parse a PDF file using the Docling Parser
    """

    def __init__(
            self,
            pipeline_options: Optional[PdfPipelineOptions] = PdfPipelineOptions(
                do_ocr=True,
                do_table_structure=True,
                table_structure_options= TableStructureOptions(
                    do_cell_matching=False,
                    mode= TableFormerMode.ACCURATE, # Or TableFormerMode.FAST
                ),
                ocr_options= EasyOcrOptions( # Or TesseractCliOcrOptions or TesseractOcrOptions
                    force_full_page_ocr=True,
                    use_gpu=False
                ), # Other options: lang, ...
                images_scale=1.0, # Needed to extract images
                generate_picture_images=True # Needed to extract images
            ),
            backend: Optional[Union[DoclingParseDocumentBackend, PyPdfiumDocumentBackend]] = DoclingParseDocumentBackend
            ):
        
        self.converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options= pipeline_options,
                    backend=backend
                )
            },
        )

    def load_documents(
            self, 
            paths: List[str], 
            raises_on_error: bool = True,
            max_num_pages: int = sys.maxsize,
            max_file_size: int = sys.maxsize,
        ) -> Generator[ConversionResult, None, None]:
        """
        """
       
        yield from self.converter.convert_all(
            paths,
            raises_on_error=raises_on_error,
            max_num_pages=max_num_pages,
            max_file_size=max_file_size,
        )

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
            **kwargs,
        ) -> List[ParserOutput]:
        """
        """
        self._validate_modalities(modalities)

        if isinstance(paths, str):
            paths = [paths]
        
        markdown_options = kwargs.get("markdown_options", {})

        raises_on_error = kwargs.get("raises_on_error", True)
        max_num_pages = kwargs.get("max_num_pages", sys.maxsize)
        max_file_size = kwargs.get("max_file_size", sys.maxsize)

        data = []
        for result in self.load_documents(paths, raises_on_error, max_num_pages, max_file_size):
            if result.status == ConversionStatus.SUCCESS:
                output = self.__export_result(result.document, modalities, markdown_options)

                data.append(output)

            else:
                raise ValueError(f"Failed to parse the document: {result.errors}")
        return data

    def __export_result(
            self, 
            document: DoclingDocument, 
            modalities: List[str],
            markdown_options: dict,
        ) -> ParserOutput:
        """
        """
        text = TextElement(text="")
        tables: List[TableElement] = []
        images: List[ImageElement] = []

        if "text" in modalities:
            text = self._extract_text(document, markdown_options)

        if any(modality in modalities for modality in ["tables", "images"]):
            for item, _ in document.iterate_items():
                if "tables" in modalities and isinstance(item, TableItem):
                    tables += self._extract_tables(item)

                if "images" in modalities and isinstance(item, PictureItem):
                    images += self._extract_images(item, document)

        return ParserOutput(text=text, tables=tables, images=images)

    @staticmethod
    def _extract_tables(item: TableItem) -> List[TableElement]:
        """
        """
        table_md: str = item.export_to_markdown()
        table_df: pd.DataFrame = item.export_to_dataframe()

        page_no = item.prov[0].page_no
        bbox = item.prov[0].bbox
        bbox = (bbox.l, bbox.t, bbox.r, bbox.b)

        return [TableElement(
            markdown=table_md,
            dataframe=table_df,
            metadata= Metadata(page_number=page_no, bbox=bbox)
            )]

    @staticmethod
    def _extract_images(item: PictureItem, doc: DoclingDocument) -> List[ImageElement]:
        """
        """
        image: Image.Image = item.get_image(doc)
        if image is None:
            return []
        page_no = item.prov[0].page_no
        bbox = item.prov[0].bbox
        bbox = (bbox.l, bbox.t, bbox.r, bbox.b)
        return [
            ImageElement(
                image=image,
                metadata= Metadata(page_number=page_no, bbox=bbox)
                )
            ]

    def _extract_text(
            self, 
            item: DoclingDocument,
            markdown_options: dict,
            ) -> TextElement:
        """
        """
        return TextElement(text=item.export_to_markdown(**markdown_options))
