import pytest
from unittest.mock import Mock, patch
import os
import pandas as pd
from PIL import Image
from parsestudio.parsers.llama_parser import LlamaPDFParser, ParserOutput, TableElement, ImageElement, Metadata, TextElement


class TestLlamaPDFParser:
    @pytest.fixture
    def parser(self):
        with patch.dict("os.environ", {"LLAMA_PARSE_KEY": "mock_api_key"}):
            return LlamaPDFParser()
        
        assert parser.converter.api_key == "mock_api_key"

    @patch.dict(os.environ, {"LLAMA_PARSE_KEY": "mock_api_key"})
    def test_init(self, parser):
        """
        Test the initialization of the LlamaPDFParser class.
        """
        llama_options = {
            "show_progress": False
        }

        with patch("parsestudio.parsers.llama_parser.LlamaParse") as mock_llama:
            mock_llama_instance = mock_llama.return_value
            mock_llama_instance.api_key = "mock_api_key"
            mock_llama_instance.show_progress = llama_options["show_progress"]

            parser = LlamaPDFParser(llama_options)
            mock_llama.assert_called_once_with(
                api_key="mock_api_key",
                **llama_options
            )



        assert parser.converter.api_key == "mock_api_key"
        assert parser.converter.show_progress == llama_options["show_progress"]


    def test_load_documents(self, parser):
        """
        Test the load_documents method when the parser is initialized and the file exists.
        """
        parser.converter = Mock()
        parser.converter.get_json_result.return_value = [{"test": "data"}]
        result = list(parser.load_documents(["test.pdf"]))
        assert result == [{"test": "data"}]


    @patch.dict(os.environ, {"LLAMA_PARSE_KEY": "mock_api_key"})
    @patch.object(LlamaPDFParser, "load_documents")
    @patch.object(LlamaPDFParser, "_LlamaPDFParser__export_result")
    def test_parse(self, mock_export, mock_load, parser):
        """
        Test the parse_and_export method by patching the load_documents and __export_result methods.
        """
        mock_document = {
            "job_id": "job123",
            "pages": [
                {
                    "page": 1,
                    "text": "Sample text",
                    "items": [
                        {
                            "type": "table",
                            "md": "| Header |\n|--------|",
                            "csv": "Header\nValue"
                        }
                    ]
                }
            ]
        }
        mock_load.return_value = [mock_document]
        mock_export.return_value = ParserOutput(
            text= TextElement(text="Sample text"),
            tables=[TableElement(
                markdown="| Header |\n|--------|", 
                dataframe=pd.DataFrame([[1, 2], [3, 4]]),
                metadata=Metadata(page_number=1)
            )],
            images=[ImageElement(
                image=Image.new("RGB", (60, 30), color="red"),
                metadata=Metadata(page_number=1)
            )]
        )

        result = parser.parse("test.pdf", ["text", "tables", "images"])
        mock_load.assert_called_once_with(["test.pdf"])
        mock_export.assert_called_once_with(mock_document, ["text", "tables", "images"])

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ParserOutput)
        assert result[0].text.text == "Sample text"
        assert len(result[0].tables) == 1
        assert len(result[0].images) == 1
        assert result[0].tables[0].markdown == "| Header |\n|--------|"
        assert result[0].tables[0].dataframe.shape == (2, 2)
        assert result[0].images[0].image.size == (60, 30)
        


    def test_extract_text(self, parser):
        page = {"text": "Test text"}
        result = parser._extract_text(page)
        assert isinstance(result, TextElement)
        assert result.text == "Test text"


    def test_extract_tables(self, parser):
        page = {
            "items": [
                {
                    "type": "table",
                    "md": "| Header |\n|--------|",
                    "csv": "Header\nValue",
                }
            ],
            "page": 1
        }
        result = parser._extract_tables(page)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TableElement)
        assert result[0].markdown == "| Header |\n|--------|"
        assert isinstance(result[0].dataframe, pd.DataFrame)
        assert isinstance(result[0].metadata, Metadata)
        assert result[0].metadata.page_number == 1

    @patch("parsestudio.parsers.llama_parser.Image.open")
    @patch("os.remove")
    def test_extract_images(self, mock_remove, mock_image_open, parser):
        """
        Test the _extract_images method by patching the Image.open and os.remove functions.
        """
        page = {"dummy": "data", "page": 1}
        job_id = "job123"

        parser.converter = Mock()
        parser.converter.get_images.return_value = [{"path": "test_image.jpg"}]
        mock_image_open.return_value.convert.return_value = Image.new("RGB", (60, 30))
        result = parser._extract_images(page, job_id)
        assert len(result) == 1
        assert isinstance(result[0], ImageElement)
        mock_remove.assert_called_once_with("test_image.jpg")
