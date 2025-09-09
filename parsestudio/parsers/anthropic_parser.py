from anthropic import Anthropic
from typing import Union, List, Generator, Dict, Optional
import pandas as pd
from PIL import Image
from io import BytesIO, StringIO
from .schemas import ParserOutput, TableElement, ImageElement, TextElement, Metadata
import json
import os
import base64
from dotenv import load_dotenv

load_dotenv()

class AnthropicPDFParser:
    """
    Parse a PDF file using Anthropic's Claude API.

    Args:
        anthropic_options (Optional[Dict]): Options for the Anthropic API client.
    
    Raises:
        ValueError: An error occurred while initializing the Anthropic client.
    """
    def __init__(
            self,
            anthropic_options: Optional[Dict] = {
                "max_tokens": 1024,
                "model": "claude-3-5-sonnet-20241022",
                "betas": ["pdfs-2024-09-25"]
            }
            ):
        try:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required")
            self.client = Anthropic(api_key=api_key)
            self.options = anthropic_options
        except ValueError as e:
            # Re-raise ValueError for missing API key or invalid configuration
            raise e
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Anthropic client: {e}")

    def load_documents(self, paths: List[str]) -> Generator[Dict, None, None]:
        """
        Load the documents from the given paths and yield the parsed result.

        Args:
            paths (List[str]): List of paths to the PDF files.
        
        Returns:
            result (Generator[Dict, None, None]): Generator yielding parsed document data
        """
        for path in paths:
            try:
                with open(path, "rb") as pdf_file:
                    pdf_data = base64.standard_b64encode(pdf_file.read()).decode("utf-8")

                response = self.client.beta.messages.create(
                    model=self.options.get("model", "claude-3-5-sonnet-20241022"),
                    betas=self.options.get("betas", ["pdfs-2024-09-25"]),
                    max_tokens=self.options.get("max_tokens", 1024),
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data
                                }
                            },
                            {
                                "type": "text",
                                "text": "Extract and structure this PDF's content with: text_content and tables (as markdown with page numbers)"
                            }
                        ]
                    }]
                )
                
                try:
                    result = {
                        "text_content": response.content[0].text,
                        "tables": []  # Tables will be extracted from the text content
                    }
                except (IndexError, AttributeError, TypeError) as e:
                    # Handle cases where response.content structure differs from expected format
                    result = {"text_content": str(response.content), "tables": []}
                
                yield result
            except Exception as e:
                print(f"Error processing file {path}: {str(e)}")
                yield {"text_content": "", "tables": []}

    def _validate_modalities(self, modalities: List[str]) -> None:
        """
        Validate the modalities provided by the user.

        Args:
            modalities (List[str]): List of modalities to validate

        Raises:
            ValueError: If the modality is not valid
        """
        valid_modalities = ["text", "tables", "images"]
        for modality in modalities:
            if modality not in valid_modalities:
                raise ValueError(f"Invalid modality: {modality}. Valid options: {valid_modalities}")

    def parse(
            self,
            paths: Union[str, List[str]],
            modalities: List[str] = ["text", "tables", "images"],
            **kwargs
        ) -> List[ParserOutput]:
        """
        Parse PDF files and extract specified modalities.

        Args:
            paths: Path or list of paths to PDF files
            modalities: List of modalities to extract. Default: ["text", "tables", "images"]
            **kwargs: Additional keyword arguments for parsing
        
        Returns:
            List[ParserOutput]: Parsed outputs
        
        Example:
        !!! example
            ```python
            parser = AnthropicPDFParser()
            data = parser.parse("file.pdf", modalities=["text", "tables"])
            text = data[0].text.text
            for table in data[0].tables:
                print(table.markdown)
                print(table.metadata.page_number)
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

    def __export_result(self, parsed_data: Dict, modalities: List[str]) -> ParserOutput:
        """
        Export parsed data to ParserOutput format.

        Args:
            parsed_data: Dictionary containing parsed content
            modalities: List of modalities to extract
        
        Returns:
            ParserOutput: Structured output with requested modalities
        """
        text = TextElement(text=parsed_data.get("text_content", "")) if "text" in modalities else TextElement(text="")
        tables = self._extract_tables(parsed_data) if "tables" in modalities else []
        images = []  # Images not supported in current API version
        return ParserOutput(text=text, tables=tables, images=images)

    @staticmethod
    def _extract_tables(parsed_data: Dict) -> List[TableElement]:
        """
        Extract tables from parsed data.

        Args:
            parsed_data: Dictionary containing parsed content

        Returns:
            List[TableElement]: List of extracted tables with metadata
        """
        tables = []
        for table in parsed_data.get("tables", []):
            try:
                markdown = table["markdown"]
                lines = markdown.split('\n')
                headers = [x.strip() for x in lines[0].split('|') if x]
                rows = []
                for line in lines[2:]:  # Skip header and separator lines
                    row = [x.strip() for x in line.split('|')[1:-1]]  # Skip first and last empty cells
                    if row:
                        rows.append(row)
                table_df = pd.DataFrame(rows, columns=headers)
                tables.append(
                    TableElement(
                        markdown=markdown,
                        dataframe=table_df,
                        metadata=Metadata(
                            page_number=table.get("page_number", 1),
                            bbox=table.get("bbox", [0, 0, 0, 0])
                        )
                    )
                )
            except (pd.errors.EmptyDataError, pd.errors.ParserError, ValueError, KeyError) as e:
                print(f"Table parsing failed - malformed data: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error processing table: {e}")
                continue
        return tables