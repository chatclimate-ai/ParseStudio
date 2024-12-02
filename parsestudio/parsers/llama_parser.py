from llama_parse import LlamaParse
import os
from typing import Generator, List, Union, Dict, Optional
import pandas as pd
from .schemas import ParserOutput, TableElement, ImageElement, TextElement, Metadata
import io
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


class LlamaPDFParser:
    """
    Parse a PDF file using the LlamaParse library.
    """
    def __init__(
            self,
            llama_options: Optional[Dict] = {
                "show_progress": True,
                "ignore_errors": False,
                "split_by_page": False,
                "invalidate_cache": False,
                "do_not_cache": False,
                "result_type": "markdown",
                "continuous_mode": True,
                "take_screenshot": True,
                "disable_ocr": False,
                "is_formatting_instruction": False,
                "premium_mode": True,
                "verbose": False
            }
            ):
        
        try:
            self.converter = LlamaParse(
                api_key=os.environ.get("LLAMA_PARSE_KEY"),
                **llama_options
            )

        except Exception as e:
            raise ValueError(
                f"An error occurred while initializing the LlamaParse converter: {e}"
            )

    def load_documents(self, paths: List[str]) -> Generator[Dict, None, None]:
        """
        Load the documents from the given paths and yield the JSON result.

        Args:
            paths (List[str]): A list of paths to the PDF files.

        Yields:
            Generator[Dict, None, None]: A generator that yields the JSON result of the document.
        """
        
        document: List[Dict] = self.converter.get_json_result(paths)
        yield from document

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
        Parse the PDF file and return the extracted data.

        Args:

        """
        self._validate_modalities(modalities)

        if isinstance(paths, str):
            paths = [paths]

        data = []
        for result in self.load_documents(paths):
            output = self.__export_result(result, modalities)
            data.append(output)

        return data

    def __export_result(
            self, 
            json_result: dict, 
            modalities: List[str]
        ) -> ParserOutput:
        """
        """
        text = TextElement(text="")
        tables: List[TableElement] = []
        images: List[ImageElement] = []

        job_id: str = json_result["job_id"]
        pages: List[Dict] = json_result["pages"]

        for page in pages:
            if "text" in modalities:
                text.text += self._extract_text(page).text + "\n"

            if "tables" in modalities:
                tables += self._extract_tables(page)

            if "images" in modalities:
                images += self._extract_images(page, job_id)

        return ParserOutput(text=text, tables=tables, images=images)

    @staticmethod
    def _extract_text(page: Dict) -> TextElement:
        """
        """
        return TextElement(text=page["text"])

    @staticmethod
    def _extract_tables(page: Dict) -> List[TableElement]:
        """
        """
        tables: List[TableElement] = []
        for item in page["items"]:
            if item["type"] == "table":
                table_md = item["md"]
                try:
                    table_df = pd.read_csv(io.StringIO(item["csv"]), sep=",")
                except Exception as e:
                    print(f"Error converting table {table_md} to dataframe: {e}")
                    table_df = None
                
                tables.append(
                    TableElement(
                        markdown=table_md, 
                        dataframe=table_df, 
                        metadata=Metadata(page_number=page["page"])
                    )
                )
        return tables

    def _extract_images(self, page: Dict, job_id: str) -> List[ImageElement]:
        """
        """
        images: List[ImageElement] = []
        image_dicts = self.converter.get_images([{
            "job_id": job_id,
            "pages": [page]
            }], download_path="llama_images")
        for img in image_dicts:
            image_path = img["path"]
            image = Image.open(image_path).convert("RGB")
            images.append(
                ImageElement(
                    image=image, 
                    metadata=Metadata(page_number=page["page"])
                    )
                )
            os.remove(image_path)
        return images
    


