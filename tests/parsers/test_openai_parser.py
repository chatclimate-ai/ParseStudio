from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest

from parsestudio.parsers.openai_file_search_parser import OpenAIFileSearchPDFParser
from parsestudio.parsers.openai_parser import OpenAIPDFParser
from parsestudio.parsers.schemas import ParserOutput, TableElement, TextElement


class TestOpenAIPDFParser:
    @pytest.fixture
    def parser(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "mock_api_key"}):
            return OpenAIPDFParser()

    @patch.dict("os.environ", {"OPENAI_API_KEY": "mock_api_key"})
    def test_init_default(self):
        with patch(
            "parsestudio.parsers.openai_file_search_parser.OpenAI"
        ) as mock_openai:
            parser = OpenAIPDFParser()
            assert isinstance(parser.parser, OpenAIFileSearchPDFParser)
            mock_openai.assert_called_once()

    @patch.dict("os.environ", {"OPENAI_API_KEY": "mock_api_key"})
    def test_init_with_options(self):
        openai_options = {"max_tokens": 2048, "model": "gpt-4o-mini"}
        with patch(
            "parsestudio.parsers.openai_file_search_parser.OpenAI"
        ) as mock_openai:
            parser = OpenAIPDFParser(openai_options=openai_options)
            assert isinstance(parser.parser, OpenAIFileSearchPDFParser)
            assert parser.parser.options["max_tokens"] == 2048
            assert parser.parser.options["model"] == "gpt-4o-mini"
            mock_openai.assert_called_once()

    def test_load_documents_structure(self, parser):
        parser.parser.client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="")]
        parser.parser.client.beta.messages.create.return_value = mock_response

        with patch("builtins.open", mock_open(read_data=b"test")):
            result = list(parser.load_documents(["test.pdf"]))
            assert len(result) == 1
            assert result[0]["text_content"] == ""
            assert result[0]["tables"] == []

    def test_validate_modalities(self, parser):
        parser._validate_modalities(["text", "tables", "images"])
        with pytest.raises(ValueError, match="Invalid modalities"):
            parser._validate_modalities(["invalid"])

    @patch("builtins.open", mock_open(read_data=b"test"))
    @patch.object(OpenAIFileSearchPDFParser, "load_documents")
    @patch.object(
        OpenAIFileSearchPDFParser, "_OpenAIFileSearchPDFParser__export_result"
    )
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
