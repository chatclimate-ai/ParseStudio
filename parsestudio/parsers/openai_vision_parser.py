from openai import OpenAI
from typing import Union, List, Generator, Dict, Optional, Any
import pandas as pd
import json
import os
import base64
import time
from dotenv import load_dotenv
from pdf2image import convert_from_path
from io import BytesIO

# Your own pydantic models (keep as-is in your project)
from .schemas import ParserOutput, TableElement, ImageElement, TextElement, Metadata

load_dotenv()

JSON_SCHEMA = {
    "name": "pdf_page_extract",
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
    "You receive a single PDF page as an image. "
    "Extract:\n"
    "1) All legible text as a single string in 'text_content'.\n"
    "2) Every table as Markdown (GitHub table format) in 'tables[].markdown'.\n"
    "- If you detect table boundaries, add an approximate pixel bbox [x1,y1,x2,y2].\n"
    "- Always return valid JSON conforming to the provided schema."
)

def _b64_image_uri(pil_image) -> str:
    buf = BytesIO()
    pil_image.save(buf, format="PNG")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

class OpenAIVisionPDFParser:
    def __init__(
        self,
        openai_options: Optional[Dict[str, Any]] = None
    ):
        # Sensible defaults: fast, good vision + JSON, cheap
        defaults = {
            "model": "gpt-4o-mini",          # or "o4-mini" if you have access
            "max_output_tokens": 4000,       # modern param
            "temperature": 0
        }
        self.options = {**defaults, **(openai_options or {})}
        try:
            # If OPENAI_API_KEY is in env, the SDK picks it up; explicit is fine too
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        except Exception as e:
            raise ValueError(f"Failed to init OpenAI client: {e}")

    def _analyze_page(self, image, page_number: int, retries: int = 3, backoff: float = 1.5) -> Dict:
        image_uri = _b64_image_uri(image)
        last_err = None
        for attempt in range(retries):
            try:
                resp = self.client.chat.completions.create(
                    model=self.options["model"],
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": f"Analyze page {page_number}."},
                                {"type": "image_url", "image_url": {"url": image_uri}}
                            ]
                        }
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": JSON_SCHEMA
                    },
                    max_tokens=self.options["max_output_tokens"],
                    temperature=self.options.get("temperature", 0),
                )

                # Chat completions API returns content in message.content
                content = resp.choices[0].message.content
                data = json.loads(content)

                # enrich page_number if model didn't set it
                for t in data.get("tables", []):
                    t.setdefault("page_number", page_number)

                return data
            except Exception as e:
                last_err = e
                time.sleep((attempt + 1) * backoff)

        # Fallback minimal structure if all retries fail
        print(f"[WARN] Page {page_number} extraction failed: {last_err}")
        return {"text_content": "", "tables": []}

    def load_documents(self, paths: List[str]) -> Generator[Dict, None, None]:
        for path in paths:
            try:
                images = convert_from_path(path)  # requires poppler installed
                combined = {"text_content": "", "tables": []}
                for i, img in enumerate(images, start=1):
                    page = self._analyze_page(img, page_number=i)
                    # prepend page header
                    combined["text_content"] += f"\n--- Page {i} ---\n{page.get('text_content','')}"
                    combined["tables"].extend(page.get("tables", []))
                yield combined
            except Exception as e:
                print(f"[ERROR] Converting/processing {path}: {e}")
                yield {"text_content": "", "tables": []}

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
        images: List[ImageElement] = []   # you can add page images here if you like
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
                # simple GitHub-table parse
                hdr = [c.strip() for c in lines[0].strip("|").split("|")]
                rows = []
                for ln in lines[2:]:
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