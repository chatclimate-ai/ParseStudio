from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from parsestudio.parsers.openai_file_search_parser import OpenAIAssistantPDFParser
from parsestudio.parsers.openai_parser import OpenAIPDFParser
from parsestudio.parsers.schemas import ParserOutput, TableElement, TextElement


class TestOpenAIPDFParser:
    @pytest.fixture
    def parser(self):
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "mock_api_key"}),
            patch("parsestudio.parsers.openai_file_search_parser.OpenAI"),
        ):
            return OpenAIPDFParser()

    @patch.dict("os.environ", {"OPENAI_API_KEY": "mock_api_key"})
    def test_init_default(self):
        with patch(
            "parsestudio.parsers.openai_file_search_parser.OpenAI"
        ) as mock_openai:
            parser = OpenAIPDFParser()
            assert isinstance(parser.parser, OpenAIAssistantPDFParser)
            mock_openai.assert_called_once()

    @patch.dict("os.environ", {"OPENAI_API_KEY": "mock_api_key"})
    def test_init_with_options(self):
        openai_options = {"max_tokens": 2048, "model": "gpt-4o-mini"}
        with patch(
            "parsestudio.parsers.openai_file_search_parser.OpenAI"
        ) as mock_openai:
            parser = OpenAIPDFParser(openai_options=openai_options)
            assert isinstance(parser.parser, OpenAIAssistantPDFParser)
            assert parser.parser.options["max_tokens"] == 2048
            assert parser.parser.options["model"] == "gpt-4o-mini"
            mock_openai.assert_called_once()

    @patch.object(OpenAIAssistantPDFParser, "load_documents")
    def test_load_documents_structure(self, mock_load_documents, parser):
        # Mock the load_documents method to return expected structure
        mock_document = {"text_content": "Sample text", "tables": []}
        mock_load_documents.return_value = [mock_document]

        result = list(parser.load_documents(["test.pdf"]))
        assert len(result) == 1
        assert result[0]["text_content"] == "Sample text"
        assert result[0]["tables"] == []

    def test_validate_modalities(self, parser):
        parser._validate_modalities(["text", "tables", "images"])
        with pytest.raises(ValueError, match="Invalid modalities"):
            parser._validate_modalities(["invalid"])

    @patch("builtins.open", mock_open(read_data=b"test"))
    @patch.object(OpenAIAssistantPDFParser, "load_documents")
    @patch.object(OpenAIAssistantPDFParser, "_OpenAIAssistantPDFParser__export_result")
    def test_parse_structure(self, mock_export, mock_load, parser):
        mock_document = {"text_content": "Sample text", "tables": []}
        mock_load.return_value = [mock_document]
        mock_export.return_value = ParserOutput(
            text=TextElement(text="Sample text"), tables=[], images=[]
        )

        result = parser.parse("test.pdf", ["text", "tables"])
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ParserOutput)
        assert hasattr(result[0], "text")
        assert hasattr(result[0], "tables")
        assert hasattr(result[0], "images")

    def test_extract_tables(self, parser):
        table_data = "| Header |\n|--------|\n| Value |"
        parsed_data = {
            "tables": [
                {"markdown": table_data, "page_number": 1, "bbox": [0, 0, 100, 100]}
            ]
        }
        result = parser.parser._extract_tables(parsed_data)
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TableElement)
        assert result[0].markdown == table_data
        assert isinstance(result[0].dataframe, pd.DataFrame)
        assert result[0].metadata.page_number == 1
        assert result[0].metadata.bbox == [0, 0, 100, 100]


class TestOpenAIAssistantPDFParser:
    @pytest.fixture
    def mock_parser(self):
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "mock_api_key"}),
            patch("parsestudio.parsers.openai_file_search_parser.OpenAI"),
        ):
            parser = OpenAIAssistantPDFParser()
            parser.assistant_id = "test_assistant_id"
            return parser

    @patch.dict("os.environ", {"OPENAI_API_KEY": "mock_api_key"})
    def test_init_missing_api_key(self):
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(
                ValueError, match="OPENAI_API_KEY environment variable is required"
            ),
        ):
            OpenAIAssistantPDFParser()

    @patch.dict("os.environ", {"OPENAI_API_KEY": "mock_api_key"})
    @patch("parsestudio.parsers.openai_file_search_parser.OpenAI")
    def test_init_with_options(self, mock_openai):
        options = {"model": "gpt-4o-mini", "temperature": 0.5}
        parser = OpenAIAssistantPDFParser(openai_options=options)
        assert parser.options["model"] == "gpt-4o-mini"
        assert parser.options["temperature"] == 0.5

    def test_validate_modalities_valid(self, mock_parser):
        # Should not raise any exception
        mock_parser._validate_modalities(["text", "tables", "images"])
        mock_parser._validate_modalities(["text"])
        mock_parser._validate_modalities(["tables", "images"])

    def test_validate_modalities_invalid(self, mock_parser):
        with pytest.raises(ValueError, match="Invalid modalities"):
            mock_parser._validate_modalities(["invalid"])
        with pytest.raises(ValueError, match="Invalid modalities"):
            mock_parser._validate_modalities(["text", "invalid", "tables"])

    def test_extract_tables_empty(self, mock_parser):
        result = mock_parser._extract_tables({"tables": []})
        assert isinstance(result, list)
        assert len(result) == 0

    def test_extract_tables_malformed(self, mock_parser):
        # Test with a table that has insufficient rows (less than 2 lines)
        parsed_data = {
            "tables": [
                {"markdown": "| Header |", "page_number": 1, "bbox": [0, 0, 100, 100]}
            ]
        }
        result = mock_parser._extract_tables(parsed_data)
        assert isinstance(result, list)
        assert len(result) == 0  # Should be skipped due to insufficient lines

    def test_extract_tables_with_multiple_tables(self, mock_parser):
        table1_data = "| Header1 |\n|--------|\n| Value1 |"
        table2_data = "| Header2 |\n|--------|\n| Value2 |"
        parsed_data = {
            "tables": [
                {"markdown": table1_data, "page_number": 1, "bbox": [0, 0, 100, 100]},
                {"markdown": table2_data, "page_number": 2, "bbox": [0, 100, 100, 200]},
            ]
        }
        result = mock_parser._extract_tables(parsed_data)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].metadata.page_number == 1
        assert result[1].metadata.page_number == 2

    @patch("builtins.open", mock_open(read_data=b"test"))
    def test_parse_single_file(self, mock_parser):
        with patch.object(mock_parser, "load_documents") as mock_load:
            mock_load.return_value = [{"text_content": "Sample text", "tables": []}]
            result = mock_parser.parse("test.pdf")
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], ParserOutput)

    @patch("builtins.open", mock_open(read_data=b"test"))
    def test_parse_multiple_files(self, mock_parser):
        with patch.object(mock_parser, "load_documents") as mock_load:
            mock_load.return_value = [
                {"text_content": "Text 1", "tables": []},
                {"text_content": "Text 2", "tables": []},
            ]
            result = mock_parser.parse(["test1.pdf", "test2.pdf"])
            assert isinstance(result, list)
            assert len(result) == 2

    def test_export_result_text_only(self, mock_parser):
        parsed = {"text_content": "Sample text", "tables": []}
        result = mock_parser._OpenAIAssistantPDFParser__export_result(parsed, ["text"])
        assert isinstance(result, ParserOutput)
        assert result.text.text == "Sample text"
        assert len(result.tables) == 0
        assert len(result.images) == 0

    def test_export_result_with_tables(self, mock_parser):
        table_data = "| Header |\n|--------|\n| Value |"
        parsed = {
            "text_content": "Sample text",
            "tables": [
                {"markdown": table_data, "page_number": 1, "bbox": [0, 0, 100, 100]}
            ],
        }
        result = mock_parser._OpenAIAssistantPDFParser__export_result(
            parsed, ["text", "tables"]
        )
        assert isinstance(result, ParserOutput)
        assert result.text.text == "Sample text"
        assert len(result.tables) == 1
        assert len(result.images) == 0

    @patch.object(OpenAIAssistantPDFParser, "_get_or_create_vector_store")
    @patch.object(OpenAIAssistantPDFParser, "_upload_file_to_vector_store")
    @patch.object(OpenAIAssistantPDFParser, "_analyze_with_assistant_api")
    @patch.object(OpenAIAssistantPDFParser, "_cleanup_resources")
    def test_load_documents_success(
        self, mock_cleanup, mock_analyze, mock_upload, mock_vector_store, mock_parser
    ):
        mock_vector_store.return_value = "vector_store_id"
        mock_upload.return_value = "file_id"
        mock_analyze.return_value = {"text_content": "Test content", "tables": []}

        result = list(mock_parser.load_documents(["test.pdf"]))

        assert len(result) == 1
        assert result[0]["text_content"] == "Test content"
        mock_vector_store.assert_called_once()
        mock_upload.assert_called_once_with("test.pdf", "vector_store_id")
        mock_analyze.assert_called_once_with("file_id")
        mock_cleanup.assert_called_once()
