from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest

from parsestudio.parsers.anthropic_parser import (
    AnthropicPDFParser,
    Metadata,
    ParserOutput,
    TableElement,
    TextElement,
)


class TestAnthropicPDFParser:
    @pytest.fixture
    def parser(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "mock_api_key"}):
            return AnthropicPDFParser()

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "mock_api_key"})
    def test_init(self):
        anthropic_options = {"max_tokens": 2048}
        with patch("parsestudio.parsers.anthropic_parser.Anthropic") as mock_anthropic:
            parser = AnthropicPDFParser(anthropic_options)
            mock_anthropic.assert_called_once()
            assert parser.options == anthropic_options

    def test_load_documents(self, parser):
        parser.client.beta = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="test")]
        parser.client.beta.messages.create.return_value = mock_response

        with patch("builtins.open", mock_open(read_data=b"test")):
            result = list(parser.load_documents(["test.pdf"]))
            assert len(result) == 1
            assert result[0]["text_content"] == "test"

    def test_validate_modalities(self, parser):
        parser._validate_modalities(["text", "tables", "images"])
        with pytest.raises(ValueError, match="Invalid modality"):
            parser._validate_modalities(["invalid"])

    @patch("builtins.open", mock_open(read_data=b"test"))
    @patch.object(AnthropicPDFParser, "load_documents")
    @patch.object(AnthropicPDFParser, "_AnthropicPDFParser__export_result")
    def test_parse(self, mock_export, mock_load, parser):
        mock_document = {
            "text_content": "Sample text",
            "tables": [{"markdown": "| Header |\n|--------|", "page_number": 1}],
        }
        mock_load.return_value = [mock_document]
        mock_export.return_value = ParserOutput(
            text=TextElement(text="Sample text"),
            tables=[
                TableElement(
                    markdown="| Header |\n|--------|",
                    dataframe=pd.DataFrame(),
                    metadata=Metadata(page_number=1),
                )
            ],
            images=[],
        )

        result = parser.parse("test.pdf", ["text", "tables"])
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].text.text == "Sample text"
        assert len(result[0].tables) == 1

    def test_extract_tables(self, parser):
        table_data = "| Header |\n|--------|\n| Value |"
        parsed_data = {"tables": [{"markdown": table_data, "page_number": 1}]}
        result = parser._extract_tables(parsed_data)
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TableElement)
        assert result[0].markdown == table_data
        assert isinstance(result[0].dataframe, pd.DataFrame)
