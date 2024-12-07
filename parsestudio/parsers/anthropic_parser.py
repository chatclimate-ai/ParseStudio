from anthropic import Anthropic
from typing import Union, List, Generator, Dict, Optional
import pandas as pd
from PIL import Image
from io import BytesIO, StringIO
from .schemas import ParserOutput, TableElement, ImageElement, TextElement, Metadata
import json
import os
from dotenv import load_dotenv

load_dotenv()

class AnthropicPDFParser:
    def __init__(
            self,
            anthropic_options: Optional[Dict] = {
                "max_tokens": 4096,
                "model": "claude-3-sonnet-20240229"
            }
            ):
        try:
            self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            self.options = anthropic_options
        except Exception as e:
            raise ValueError(f"An error occurred while initializing the Anthropic client: {e}")

    def load_documents(self, paths: List[str]) -> Generator[Dict, None, None]:
        for path in paths:
            with open(path, 'rb') as f:
                response = self.client.messages.create(
                    model=self.options.get("model", "claude-3-sonnet-20240229"),
                    max_tokens=self.options.get("max_tokens", 4096),
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract and structure this PDF's content with: text_content, tables (as markdown with page numbers)"},
                            {"type": "file", "file_path": path}
                        ],
                    }]
                )
                try:
                    result = json.loads(response.content)
                except:
                    result = {"text_content": response.content, "tables": []}
                yield result

    def _validate_modalities(self, modalities: List[str]) -> None:
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
        self._validate_modalities(modalities)
        if isinstance(paths, str):
            paths = [paths]
        data = []
        for result in self.load_documents(paths):
            output = self.__export_result(result, modalities)
            data.append(output)
        return data

    def __export_result(self, parsed_data: Dict, modalities: List[str]) -> ParserOutput:
        text = TextElement(text=parsed_data.get("text_content", "")) if "text" in modalities else TextElement(text="")
        tables = self._extract_tables(parsed_data) if "tables" in modalities else []
        images = []
        return ParserOutput(text=text, tables=tables, images=images)

    @staticmethod
    def _extract_tables(parsed_data: Dict) -> List[TableElement]:
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
            except Exception as e:
                print(f"Error processing table: {e}")
                continue
        return tables
