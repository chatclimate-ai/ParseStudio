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

    Args:
        llama_options (Optional[Dict], optional): A dictionary containing the options for the LlamaParse converter.
    
    Raises:
        ValueError: An error occurred while initializing the LlamaParse converter.
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
            result (Generator[Dict, None, None]): A generator that yields the JSON result of the document.
        """
        
        document: List[Dict] = self.converter.get_json_result(paths)
        yield from document

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
            parser = LlamaPDFParser()
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

    def __export_result(
            self, 
            json_result: dict, 
            modalities: List[str]
        ) -> ParserOutput:
        """
        Export the result to the ParserOutput object.

        Args:
            json_result (dict): The JSON result of the document.
            modalities (List[str]): List of modalities to extract.
        
        Returns:
            output (ParserOutput): The ParserOutput object containing the extracted modalities.
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
        Extract the text from the page dict.

        Args:
            page (Dict): A dictionary containing the page information.

        Returns:
            text (TextElement): TextElement object
        
        Examples:
        !!! example
            ```python
            parser = LlamaPDFParser()
            text = parser._extract_text(page)
            text = text.text
            ```
        """
        return TextElement(text=page["text"])

    @staticmethod
    def _extract_tables(page: Dict) -> List[TableElement]:
        """
        Extract the tables from the page dict.

        Args:
            page (Dict): A dictionary containing the page information.
        
        Returns:
            tables (List[TableElement]): List of TableElement objects
        
        Examples:
        !!! example
            ```python
            parser = LlamaPDFParser()
            table = parser._extract_tables(table_item)[0]
            table_md = table.markdown
            table_df = table.dataframe
            page_number = table.metadata.page_number
            bbox = table.metadata.bbox
            ```
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
        Extract the images from the page dict.

        Args:
            page (Dict): A dictionary containing the page information.
            job_id (str): The job_id of the document.

        Returns:
            images (List[ImageElement]): List of ImageElement objects

        Examples:
        !!! example
            ```python
            parser = LlamaPDFParser()
            image = parser._extract_images(page, job_id)[0]
            image_obj = image.image
            page_number = image.metadata.page_number
            bbox = image.metadata.bbox
            ```
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
    


