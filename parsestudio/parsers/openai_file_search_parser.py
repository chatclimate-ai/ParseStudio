import json
import os
import time
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    try:
        from openai.types.beta import AssistantToolParam
    except ImportError:
        AssistantToolParam = type[dict[str, Any]]
else:
    AssistantToolParam = Any

import openai
import pandas as pd
import srsly
from dotenv import load_dotenv
from jinja2 import Template
from openai import OpenAI

from parsestudio.logging_config import get_logger

from .schemas import ImageElement, Metadata, ParserOutput, TableElement, TextElement
from .templates import read_template

load_dotenv()
logger = get_logger("parsers.openai_assistant")

OPENAI_EXTRACTION_TEMPLATE = read_template("openai_extraction")


def _load_extraction_function_tool() -> dict[str, Any]:
    """Load JSON schema and convert to function tool definition."""
    schema_path = Path(__file__).parent / "tools" / "openai_extraction.json"
    try:
        schema = srsly.read_json(schema_path)
        # Convert JSON schema to function tool definition
        return {
            "type": "function",
            "function": {
                "name": "extract_pdf_content",
                "description": "Extract structured content from PDF including text and tables in the specified format",
                "parameters": schema,
            },
        }
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise RuntimeError(
            f"Failed to load extraction function tool from {schema_path}: {e}"
        ) from e


EXTRACTION_FUNCTION_TOOL = _load_extraction_function_tool()


class OpenAIAssistantPDFParser:
    def __init__(self, openai_options: dict[str, Any] | None = None):
        # Sensible defaults for Assistant API
        defaults = {"model": "gpt-4o", "temperature": 0}
        self.options = {**defaults, **(openai_options or {})}
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self.client = OpenAI(api_key=api_key)
            self.assistant_id: str | None = os.environ.get("ASSISTANT_ID_PARSER2")
            self.vector_store_id: str | None = None  # Will be created for file search
        except ValueError as e:
            # Re-raise ValueError for missing API key or invalid configuration
            raise e
        except Exception as e:
            raise ConnectionError(f"Failed to initialize OpenAI client: {e}") from e

        # Initialize assistant
        self._initialize_assistant()

    def _initialize_assistant(self) -> None:
        """Initialize or create the OpenAI Assistant."""
        instructions = Template(OPENAI_EXTRACTION_TEMPLATE).render()

        if not self.assistant_id:
            self._create_assistant(instructions)
        else:
            try:
                self.client.beta.assistants.retrieve(assistant_id=self.assistant_id)
                logger.info(f"Using existing assistant with ID: {self.assistant_id}")
                self._update_assistant(instructions)
            except Exception as e:
                logger.warning(
                    f"Error retrieving assistant: {e}. Creating new assistant."
                )
                self._create_assistant(instructions)

    def _create_assistant(self, instructions: str) -> None:
        """Create a new OpenAI Assistant with file search capabilities."""
        try:
            tools: list[AssistantToolParam] = [
                {"type": "file_search", "file_search": {"max_num_results": 20}},
                EXTRACTION_FUNCTION_TOOL,
            ]

            assistant = self.client.beta.assistants.create(
                name="PDF Extraction Assistant",
                instructions=instructions,
                model=self.options["model"],
                tools=tools,
                response_format={"type": "json_object"},
            )

            self.assistant_id = assistant.id
            logger.info(f"Created new assistant with ID: {self.assistant_id}")
        except openai.AuthenticationError as e:
            raise ValueError(f"Invalid OpenAI API key: {e}") from e
        except openai.RateLimitError as e:
            raise RuntimeError(f"OpenAI API rate limit exceeded: {e}") from e
        except openai.APIError as e:
            raise RuntimeError(f"OpenAI API error creating assistant: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to create assistant: {e}") from e

    def _update_assistant(self, instructions: str) -> None:
        """Update existing assistant with new instructions."""
        try:
            tools: list[AssistantToolParam] = [
                {"type": "file_search", "file_search": {"max_num_results": 20}},
                EXTRACTION_FUNCTION_TOOL,
            ]

            if self.assistant_id is not None:
                self.client.beta.assistants.update(
                    assistant_id=self.assistant_id,
                    instructions=instructions,
                    model=self.options["model"],
                    tools=tools,
                    response_format={"type": "json_object"},
                )
            logger.info(f"Updated assistant with ID: {self.assistant_id}")
        except Exception as e:
            logger.warning(f"Error updating assistant: {e}")

    def _get_or_create_vector_store(self) -> str:
        """Create or reuse a vector store for file search."""
        if self.vector_store_id:
            return self.vector_store_id

        try:
            vector_store = self.client.vector_stores.create(
                name=f"pdf_analysis_{int(time.time())}"
            )
            self.vector_store_id = str(vector_store.id)

            # Attach vector store to assistant
            if self.assistant_id is not None:
                self.client.beta.assistants.update(
                    assistant_id=self.assistant_id,
                    tool_resources={
                        "file_search": {"vector_store_ids": [self.vector_store_id]}
                    },
                )

            return self.vector_store_id
        except openai.AuthenticationError as e:
            raise ValueError(f"Invalid OpenAI API key: {e}") from e
        except openai.RateLimitError as e:
            raise RuntimeError(f"OpenAI API rate limit exceeded: {e}") from e
        except openai.APIError as e:
            raise RuntimeError(f"OpenAI API error creating vector store: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to create vector store: {e}") from e

    def _upload_file_to_vector_store(self, file_path: str, vector_store_id: str) -> str:
        """Upload PDF file to OpenAI and add to vector store."""
        try:
            with open(file_path, "rb") as file:
                # Upload file for assistants
                response = self.client.files.create(file=file, purpose="assistants")
                file_id = str(response.id)

                # Add file to vector store
                self.client.vector_stores.files.create(
                    vector_store_id=vector_store_id, file_id=file_id
                )

                # Wait for file processing
                max_retries = 10
                for _ in range(max_retries):
                    vector_file = self.client.vector_stores.files.retrieve(
                        vector_store_id=vector_store_id, file_id=file_id
                    )
                    if vector_file.status == "completed":
                        break
                    if vector_file.status == "failed":
                        raise RuntimeError(
                            f"File processing failed: {vector_file.last_error}"
                        )
                    time.sleep(2)

            return file_id
        except (OSError, FileNotFoundError, PermissionError) as e:
            raise ValueError(f"File access error for {file_path}: {e}") from e
        except openai.AuthenticationError as e:
            raise ValueError(f"Invalid OpenAI API key: {e}") from e
        except openai.RateLimitError as e:
            raise RuntimeError(f"OpenAI API rate limit exceeded: {e}") from e
        except openai.APIError as e:
            raise RuntimeError(f"OpenAI API error during file upload: {e}") from e
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error uploading file {file_path}: {e}"
            ) from e

    def _analyze_with_assistant_api(
        self, file_id: str, retries: int = 3
    ) -> dict[str, Any]:
        """Analyze PDF content using the Assistant API."""
        last_err: Exception | None = None

        instructions = "Extract all text content and tables from the PDF document. Use the extract_pdf_content function to provide the structured output in the specified JSON format."

        for attempt in range(retries):
            thread_id = None
            try:
                # Create thread with file attachment
                thread = self.client.beta.threads.create(
                    messages=[
                        {
                            "role": "user",
                            "content": instructions,
                            "attachments": [
                                {"file_id": file_id, "tools": [{"type": "file_search"}]}
                            ],
                        }
                    ]
                )
                thread_id = thread.id

                # Create run
                if self.assistant_id is None:
                    raise RuntimeError("Assistant ID not available")
                run = self.client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=self.assistant_id,
                    instructions=instructions,
                )

                # Poll for completion
                start_time = time.time()
                max_duration = 180  # 3 minutes
                poll_interval = 3
                function_call_count = 0
                last_function_result: dict[str, Any] | None = None

                while True:
                    elapsed_time = time.time() - start_time
                    if elapsed_time > max_duration:
                        if last_function_result:
                            return last_function_result
                        raise RuntimeError(
                            f"Request timed out after {int(elapsed_time)} seconds"
                        )

                    run_status = self.client.beta.threads.runs.retrieve(
                        thread_id=thread_id, run_id=run.id
                    )

                    if (
                        run_status.status == "requires_action"
                        and run_status.required_action is not None
                        and run_status.required_action.type == "submit_tool_outputs"
                    ):
                        tool_calls = (
                            run_status.required_action.submit_tool_outputs.tool_calls
                        )
                        tool_outputs = []
                        function_call_count += 1

                        for tool_call in tool_calls:
                            if tool_call.function.name == "extract_pdf_content":
                                try:
                                    args: dict[str, Any] = json.loads(
                                        tool_call.function.arguments
                                    )
                                    last_function_result = args

                                    if function_call_count >= 2:
                                        return args

                                    tool_outputs.append(
                                        {
                                            "tool_call_id": tool_call.id,
                                            "output": json.dumps(
                                                {
                                                    "status": "processing",
                                                    "message": "Continue with content extraction",
                                                }
                                            ),
                                        }
                                    )
                                except Exception as e:
                                    tool_outputs.append(
                                        {
                                            "tool_call_id": tool_call.id,
                                            "output": json.dumps({"error": str(e)}),
                                        }
                                    )

                        if tool_outputs:
                            self.client.beta.threads.runs.submit_tool_outputs(
                                thread_id=thread_id,
                                run_id=run.id,
                                tool_outputs=tool_outputs,
                            )
                            continue

                    elif run_status.status == "completed":
                        if last_function_result:
                            return last_function_result

                        messages = self.client.beta.threads.messages.list(
                            thread_id=thread_id
                        )
                        if messages.data and messages.data[0].content:
                            content_block = messages.data[0].content[0]
                            if hasattr(content_block, "text") and hasattr(
                                content_block.text, "value"
                            ):
                                content = content_block.text.value
                            else:
                                content = str(content_block)
                            try:
                                # Try to parse as JSON
                                if content.startswith("{"):
                                    parsed_content: dict[str, Any] = json.loads(content)
                                    return parsed_content
                            except json.JSONDecodeError:
                                pass
                            return {"text_content": content, "tables": []}
                        return {"text_content": "", "tables": []}

                    elif run_status.status in ["failed", "cancelled", "expired"]:
                        if last_function_result:
                            return last_function_result
                        raise RuntimeError(
                            f"Assistant run failed with status: {run_status.status}"
                        )

                    time.sleep(poll_interval)

            except openai.AuthenticationError as e:
                raise ValueError(f"Invalid OpenAI API key: {e}") from e
            except openai.RateLimitError as e:
                last_err = e
                time.sleep((attempt + 1) * 2.0)
            except (openai.APIError, json.JSONDecodeError, KeyError) as e:
                last_err = e
                logger.warning(
                    f"API error on attempt {attempt + 1}",
                    extra={"error": str(e), "type": type(e).__name__},
                )
                time.sleep((attempt + 1) * 1.5)
            except Exception as e:
                last_err = e
                logger.warning(
                    f"Unexpected error on attempt {attempt + 1}",
                    extra={"error": str(e), "type": type(e).__name__},
                )
                time.sleep((attempt + 1) * 1.5)
            finally:
                # Clean up thread
                if thread_id:
                    try:
                        self.client.beta.threads.delete(thread_id)
                    except Exception as e:
                        logger.warning(f"Failed to delete thread {thread_id}: {e}")

        logger.warning(
            "Assistant API analysis failed after retries",
            extra={"error": str(last_err), "retries": retries},
        )
        return {"text_content": "", "tables": []}

    def _cleanup_resources(
        self, file_ids: list[str], vector_store_id: str | None
    ) -> None:
        """Clean up uploaded files and vector store."""
        try:
            # Delete vector store (this also removes file associations)
            if vector_store_id:
                try:
                    self.client.vector_stores.delete(vector_store_id)
                except Exception as e:
                    logger.warning(
                        "Failed to delete vector store",
                        extra={"vector_store_id": vector_store_id, "error": str(e)},
                    )

            # Delete uploaded files
            for file_id in file_ids:
                try:
                    self.client.files.delete(file_id)
                except Exception as e:
                    logger.warning(
                        "Failed to delete file",
                        extra={"file_id": file_id, "error": str(e)},
                    )
        except Exception as e:
            logger.warning("Resource cleanup failed", extra={"error": str(e)})

    def load_documents(self, paths: list[str]) -> Generator[dict[str, Any], None, None]:
        """Load and analyze PDF documents using OpenAI Assistant API with file search."""
        for path in paths:
            file_ids = []
            vector_store_id = None

            try:
                # Create vector store
                vector_store_id = self._get_or_create_vector_store()

                # Upload file to vector store
                file_id = self._upload_file_to_vector_store(path, vector_store_id)
                file_ids.append(file_id)

                # Analyze with Assistant API
                result = self._analyze_with_assistant_api(file_id)

                yield result

            except Exception as e:
                logger.error(
                    "Failed to process PDF file",
                    extra={
                        "file_path": path,
                        "error": str(e),
                        "parser": "openai_assistant",
                    },
                )
                yield {"text_content": "", "tables": []}

            finally:
                # Always cleanup resources
                self._cleanup_resources(file_ids, vector_store_id)

    def _validate_modalities(self, modalities: list[str]) -> None:
        valid = {"text", "tables", "images"}
        invalid = [m for m in modalities if m not in valid]
        if invalid:
            raise ValueError(f"Invalid modalities: {invalid}. Valid: {sorted(valid)}")

    def parse(
        self,
        paths: str | list[str],
        modalities: list[str] | None = None,
        **kwargs: Any,
    ) -> list[ParserOutput]:
        if modalities is None:
            modalities = ["text", "tables", "images"]
        self._validate_modalities(modalities)
        # kwargs reserved for future use
        if isinstance(paths, str):
            paths = [paths]
        outputs: list[ParserOutput] = []
        for result in self.load_documents(paths):
            outputs.append(self.__export_result(result, modalities))
        return outputs

    def __export_result(
        self, parsed: dict[str, Any], modalities: list[str]
    ) -> ParserOutput:
        text = (
            TextElement(text=parsed.get("text_content", ""))
            if "text" in modalities
            else TextElement(text="")
        )
        tables = self._extract_tables(parsed) if "tables" in modalities else []
        images: list[ImageElement] = []  # Assistant API doesn't extract images
        return ParserOutput(text=text, tables=tables, images=images)

    @staticmethod
    def _extract_tables(parsed: dict[str, Any]) -> list[TableElement]:
        out: list[TableElement] = []
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

                df = (
                    pd.DataFrame(rows, columns=hdr)
                    if rows
                    else pd.DataFrame(columns=hdr)
                )

                out.append(
                    TableElement(
                        markdown=md,
                        dataframe=df,
                        metadata=Metadata(
                            page_number=tbl.get("page_number", 1),
                            bbox=tbl.get("bbox", [0, 0, 0, 0]),
                        ),
                    )
                )
            except (pd.errors.EmptyDataError, pd.errors.ParserError, ValueError) as e:
                logger.warning(
                    "Table parsing failed - malformed data",
                    extra={"error": str(e), "parser": "openai_assistant"},
                )
            except Exception as e:
                logger.error(
                    "Unexpected table parsing error",
                    extra={"error": str(e), "parser": "openai_assistant"},
                )
        return out
