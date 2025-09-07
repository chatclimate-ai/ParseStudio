from openai import OpenAI
from typing import Union, List, Generator, Dict, Optional, Any
import pandas as pd
import json
import os
import time
from dotenv import load_dotenv

from .schemas import ParserOutput, TableElement, ImageElement, TextElement, Metadata

load_dotenv()

JSON_SCHEMA = {
    "name": "pdf_content_extract",
    "schema": {
        "type": "object",
        "properties": {
            "text_content": {"type": "string"},
            "tables": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "markdown": {"type": "string"},
                        "page_number": {"type": "integer"},
                        "bbox": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 4,
                            "maxItems": 4
                        }
                    },
                    "required": ["markdown"]
                }
            }
        },
        "required": ["text_content", "tables"],
        "additionalProperties": False,
    },
    "strict": True
}

SYSTEM_PROMPT = (
    "You are an expert PDF content analyzer. Extract and structure the content from the provided PDF file. "
    "Return:\n"
    "1) All text content as a single comprehensive string in 'text_content'\n"
    "2) All tables found in the document as Markdown format in 'tables[].markdown'\n"
    "3) For tables, estimate page numbers and bounding boxes if possible\n"
    "Always return valid JSON conforming to the provided schema."
)

class OpenAIFileSearchPDFParser:
    def __init__(
        self,
        openai_options: Optional[Dict[str, Any]] = None
    ):
        # Sensible defaults for file search approach
        defaults = {
            "model": "gpt-4o-mini",
            "max_tokens": 4000,
            "temperature": 0
        }
        self.options = {**defaults, **(openai_options or {})}
        try:
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        except Exception as e:
            raise ValueError(f"Failed to init OpenAI client: {e}")

    def _upload_file_to_openai(self, file_path: str) -> str:
        """Upload PDF file to OpenAI and return file ID."""
        try:
            with open(file_path, "rb") as file:
                response = self.client.files.create(
                    file=file,
                    purpose="assistants"
                )
            return response.id
        except Exception as e:
            raise ValueError(f"Failed to upload file {file_path}: {e}")

    def _create_vector_store(self, file_ids: List[str]) -> str:
        """Create vector store with uploaded files."""
        try:
            vector_store = self.client.vector_stores.create(
                name=f"pdf_analysis_{int(time.time())}"
            )
            
            # Add files to vector store
            for file_id in file_ids:
                self.client.vector_stores.files.create(
                    vector_store_id=vector_store.id,
                    file_id=file_id
                )
            
            return vector_store.id
        except Exception as e:
            raise ValueError(f"Failed to create vector store: {e}")

    def _analyze_with_file_search(self, vector_store_id: str, retries: int = 3) -> Dict:
        """Analyze PDF content using file search."""
        last_err = None
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.options["model"],
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": "Analyze the uploaded PDF file and extract all text content and tables according to the schema."}
                    ],
                    tools=[{
                        "type": "file_search",
                        "file_search": {
                            "vector_store_ids": [vector_store_id]
                        }
                    }],
                    response_format={
                        "type": "json_schema",
                        "json_schema": JSON_SCHEMA
                    },
                    max_tokens=self.options["max_tokens"],
                    temperature=self.options.get("temperature", 0),
                )

                content = response.choices[0].message.content
                return json.loads(content)
            except Exception as e:
                last_err = e
                time.sleep((attempt + 1) * 1.5)

        # Fallback minimal structure if all retries fail
        print(f"[WARN] File search analysis failed: {last_err}")
        return {"text_content": "", "tables": []}

    def _cleanup_resources(self, file_ids: List[str], vector_store_id: str):
        """Clean up uploaded files and vector store."""
        try:
            # Delete vector store
            if vector_store_id:
                self.client.vector_stores.delete(vector_store_id)
            
            # Delete uploaded files
            for file_id in file_ids:
                try:
                    self.client.files.delete(file_id)
                except Exception as e:
                    print(f"[WARN] Failed to delete file {file_id}: {e}")
        except Exception as e:
            print(f"[WARN] Cleanup failed: {e}")

    def load_documents(self, paths: List[str]) -> Generator[Dict, None, None]:
        """Load and analyze PDF documents using OpenAI file search."""
        for path in paths:
            file_ids = []
            vector_store_id = None
            
            try:
                # Upload file
                file_id = self._upload_file_to_openai(path)
                file_ids.append(file_id)
                
                # Create vector store
                vector_store_id = self._create_vector_store(file_ids)
                
                # Analyze with file search
                result = self._analyze_with_file_search(vector_store_id)
                
                yield result

            except Exception as e:
                print(f"[ERROR] Processing {path}: {e}")
                yield {"text_content": "", "tables": []}
                
            finally:
                # Always cleanup resources
                self._cleanup_resources(file_ids, vector_store_id)

    def _validate_modalities(self, modalities: List[str]) -> None:
        valid = {"text", "tables", "images"}
        invalid = [m for m in modalities if m not in valid]
        if invalid:
            raise ValueError(f"Invalid modalities: {invalid}. Valid: {sorted(valid)}")

    def parse(
        self,
        paths: Union[str, List[str]],
        modalities: List[str] = ["text", "tables", "images"],
        **kwargs
    ) -> List[ParserOutput]:
        self._validate_modalities(modalities)
        if isinstance(paths, str):
            paths = [paths]
        outputs: List[ParserOutput] = []
        for result in self.load_documents(paths):
            outputs.append(self.__export_result(result, modalities))
        return outputs

    def __export_result(self, parsed: Dict, modalities: List[str]) -> ParserOutput:
        text = TextElement(text=parsed.get("text_content", "")) if "text" in modalities else TextElement(text="")
        tables = self._extract_tables(parsed) if "tables" in modalities else []
        images: List[ImageElement] = []  # File search doesn't extract images
        return ParserOutput(text=text, tables=tables, images=images)

    @staticmethod
    def _extract_tables(parsed: Dict) -> List[TableElement]:
        out: List[TableElement] = []
        for tbl in parsed.get("tables", []):
            try:
                md = tbl["markdown"]
                lines = [ln for ln in md.splitlines() if ln.strip()]
                if len(lines) < 2:
                    continue
                
                # Parse GitHub-style markdown table
                hdr = [c.strip() for c in lines[0].strip("|").split("|")]
                rows = []
                for ln in lines[2:]:  # Skip separator line
                    cells = [c.strip() for c in ln.strip("|").split("|")]
                    if cells and any(cells):
                        rows.append(cells)
                
                df = pd.DataFrame(rows, columns=hdr) if rows else pd.DataFrame(columns=hdr)

                out.append(
                    TableElement(
                        markdown=md,
                        dataframe=df,
                        metadata=Metadata(
                            page_number=tbl.get("page_number", 1),
                            bbox=tbl.get("bbox", [0, 0, 0, 0])
                        )
                    )
                )
            except Exception as e:
                print(f"[WARN] Table parse failed: {e}")
        return out