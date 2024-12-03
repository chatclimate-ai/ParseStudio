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

    Args:
        pipeline_options (PdfPipelineOptions): Options for the PDF pipeline. 
        backend (Union[DoclingParseDocumentBackend, PyPdfiumDocumentBackend]): Backend to use for parsing the PDF.

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
        Load the documents from the given paths and convert them to DoclingDocument objects.

        Args:
            paths (List[str]): List of paths to the documents
            raises_on_error (bool): Whether to raise an error if the conversion fails. Default is True
            max_num_pages (int): Maximum number of pages to convert. Default is sys.maxsize
            max_file_size (int): Maximum file size to convert. Default is sys.maxsize
        
        Returns:
            result (Generator[ConversionResult, None, None]): Generator of ConversionResult objects
        """
       
        yield from self.converter.convert_all(
            paths,
            raises_on_error=raises_on_error,
            max_num_pages=max_num_pages,
            max_file_size=max_file_size,
        )

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
            **kwargs,
        ) -> List[ParserOutput]:
        """
        Parse the documents and extract the specified modalities.

        Args:
            paths (Union[str, List[str]]): Path or list of paths to the documents
            modalities (List[str]): List of modalities to extract. Default is ["text", "tables", "images"]
            **kwargs: Keyword arguments to pass to the export_to_markdown method. For example, markdown_options={"image_placeholder": "<image>"}
        
        Returns:
            data (List[ParserOutput]): List of ParserOutput objects
        
        Raises:
            ValueError: If the modality is not valid
        
        Examples:
        !!! example
            ```python
            parser = DoclingPDFParser()
            data = parser.parse("path/to/document.pdf", modalities=["text", "tables", "images"])
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
        Export the result the ParserOutput object.

        Args:
            document (DoclingDocument): DoclingDocument object
            modalities (List[str]): List of modalities to extract
            markdown_options (dict): Options to pass to the export_to_markdown method
        
        Returns:
            output (ParserOutput): ParserOutput object
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
        Extract the tables from the TableItem object.

        Args:
            item (TableItem): TableItem object
        
        Returns:
            tables (List[TableElement]): List of TableElement objects
        
        Examples:
        !!! example
            ```python
            parser = DoclingPDFParser()
            table = parser._extract_tables(table_item)[0]
            table_md = table.markdown
            table_df = table.dataframe
            page_number = table.metadata.page_number
            bbox = table.metadata.bbox
            ```
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
        Extract the images from the PictureItem object.

        Args:
            item (PictureItem): PictureItem object
            doc (DoclingDocument): DoclingDocument object
        
        Returns:
            images (List[ImageElement]): List of ImageElement objects
        
        Examples:
        !!! example
            ```python
            parser = DoclingPDFParser()
            image = parser._extract_images(picture_item, doc)[0]
            image_obj = image.image
            page_number = image.metadata.page_number
            bbox = image.metadata.bbox
            ``` 
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
        Extract the text from the DoclingDocument object.

        Args:
            item (DoclingDocument): DoclingDocument object
            markdown_options (dict): Options to pass to the export_to_markdown method
        
        Returns:
            text (TextElement): TextElement object
        
        Examples:
        !!! example
            ```python
            parser = DoclingPDFParser()
            text = parser._extract_text(doc, markdown_options= {
                "image_mode": ImageRefMode.EMBEDDED # embed the images in the markdown
            })
            text = text.text
            ```
        """
        return TextElement(text=item.export_to_markdown(**markdown_options))
