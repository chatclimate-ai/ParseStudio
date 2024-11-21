from llama_parse import LlamaParse
import os
from typing import Generator, List, Union, Dict
import pandas as pd
from .schema import ParserOutput
import io
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


class LlamaPDFParser:
    """
    Parse a PDF file using the LlamaParse library.
    """
    def __init__(self):
        self.initialized = False

    def __initialize_llama(self, **kwargs) -> None:
        """
        Initialize the LlamaParse converter with the given options.

        Args:
            language (str): The language of the document. Default is "en".
            result_type (str): The type of result to return. Default is "markdown".
            continuous_mode (bool): Whether to use continuous mode while parsing. Default is True.
            take_screenshot (bool): Whether to take screenshots of the document pages. Default is False.
            disable_ocr (bool): Whether to disable OCR. Default is False.
            is_formatting_instruction (bool): Whether to use the formatting instruction. Default is False.
            show_progress (bool): Whether to show progress bar. Default is False.
            ignore_errors (bool): Whether to ignore errors while parsing. Default is False.
            split_by_page (bool): Whether to split the results by page or not. Default is False.
            invalidate_cache (bool): Whether to invalidate the cache. Default is False.
            do_not_cache (bool): Whether to not cache the results. Default is False.
        """
        try:
            self.converter = LlamaParse(
                api_key=os.environ.get("LLAMA_PARSE_KEY"),
                show_progress=False,
                ignore_errors=False,
                split_by_page = False,
                invalidate_cache=True,
                do_not_cache=True,
                **kwargs,
            )

            self.initialized = True

        except Exception as e:
            raise ValueError(
                f"An error occurred while initializing the LlamaParse converter: {e}"
            )

    def load_documents(self, paths: List[str]) -> Generator[Dict, None, None]:
        """
        Load the given documents and parse them. The documents are parsed in parallel.

        Args:
            paths (List[str]): The list of paths to the PDF files.

        Returns:
            documents (Generator[Dict, None, None]): A generator that yields the parsed documents.
        """
        if not self.initialized:
            raise ValueError("The Docling Parser has not been initialized.")

        if isinstance(paths, str):
            paths = [paths]

        for path in paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"The file {path} does not exist.")

            if not path.endswith(".pdf"):
                raise ValueError(f"The file {path} must be a PDF file.")

        document: List[Dict] = self.converter.get_json_result(paths)
        yield from document

    def parse_and_export(
        self,
        paths: Union[str, List[str]],
        modalities: List[str] = ["text", "tables", "images"],
        **kwargs,
    ) -> List[ParserOutput]:
        """
        Parse the given documents and export the parsed results in the specified modalities. The parsed results are exported as a ParserOutput object.

        Args:
            paths (Union[str, List[str]]): The path to the PDF file or a list of paths to the PDF files.
            modalities (List[str]): The list of modalities to export. Default is ["text", "tables", "images"].
            language (str): The language of the document. Default is "en".
            result_type (str): The type of result to return. Default is "markdown".
            continuous_mode (bool): Whether to use continuous mode while parsing. Default is True.
            take_screenshot (bool): Whether to take screenshots of the document pages. Default is False.
            disable_ocr (bool): Whether to disable OCR. Default is False.
            is_formatting_instruction (bool): Whether to use the formatting instruction. Default is False.
        
        Returns:
            data (List[ParserOutput]): A list of ParserOutput objects containing the parsed results.
        
        
        Example:
            >>> parser = LlamaPDFParser()
            >>> data = parser.parse_and_export("path/to/pdf/file.pdf", modalities=["text", "tables", "images"])
            >>> print(data)
            ... [ParserOutput(text="...", tables=[...], images=[...])]

        """
        if isinstance(paths, str):
            paths = [paths]

        if not self.initialized:
            language = kwargs.get("language", "en")
            result_type = kwargs.get("result_type", "markdown")
            continuous_mode = kwargs.get("continuous_mode", True)
            take_screenshot = kwargs.get("take_screenshot", False)
            disable_ocr = kwargs.get("disable_ocr", False)
            is_formatting_instruction = kwargs.get("is_formatting_instruction", False)

            self.__initialize_llama(
                language=language,
                result_type=result_type,
                continuous_mode=continuous_mode,
                take_screenshot=take_screenshot,
                disable_ocr=disable_ocr,
                is_formatting_instruction=is_formatting_instruction,
            )

        data = []
        for result in self.load_documents(paths):
            output = self.__export_result(result, modalities)
            data.append(output)

        return data

    def __export_result(self, json_result: dict, modalities: List[str]) -> ParserOutput:
        """
        Export the parsed result for a given document to the ParserOutput schema.

        Args:
            json_result (dict): The parsed result of the document.
            modalities (List[str]): The list of modalities to export.
        
        Returns:
            output (ParserOutput): The parsed result exported as a ParserOutput object.
        """
        text = ""
        tables: List[Dict] = []
        images: List[Dict] = []

        pages: List[Dict] = json_result["pages"]

        for page in pages:
            if "text" in modalities:
                text += self._extract_text(page) + "\n"

            if "tables" in modalities:
                tables += self._extract_tables(page)

            if "images" in modalities:
                images += self._extract_images(page)

        return ParserOutput(text=text, tables=tables, images=images)

    @staticmethod
    def _extract_text(page: Dict) -> str:
        """
        Extract text from a page.

        Args:
            page (Dict): The page dictionary containing the text data.
        
        Returns:
            text (str): The extracted text from the page.
        """
        return page["text"]

    @staticmethod
    def _extract_tables(page: Dict) -> List[Dict]:
        """
        Extract tables from the document and return as a list of dictionaries with with table markdown and dataframe data.

        Args:
            page (Dict): The page dictionary containing the table data.
        
        Returns:
            tables (List[Dict]): A list of dictionaries with table data. Each dictionary contains a markdown table (table_md) and a pandas dataframe (table_df).
        """
        tables = []
        for item in page["items"]:
            if item["type"] == "table":
                table_md = item["md"]
                table_df = pd.read_csv(io.StringIO(item["csv"]), sep=",")

                tables.append({"table_md": table_md, "table_df": table_df})
        return tables

    def _extract_images(self, page: Dict) -> List[Dict]:
        """
        Extract images from a page and return as a list of dictionaries with image data.

        Args:
            page (Dict): The page dictionary containing the image data.
        
        Returns:
            images (List[Dict]): A list of dictionaries with image data. Each dictionary contains the key "image" with the value as a PIL Image object.
        """
        images = []
        image_dicts = self.converter.get_images([page], download_path="llama_images")
        for img in image_dicts:
            image_path = img["path"]
            image = Image.open(image_path).convert("RGB")
            images.append({"image": image})
            os.remove(image_path)
        return images
