import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import pandas as pd
from PIL import Image
from io import StringIO
from parseval.parsers.llama_parser import LlamaPDFParser, ParserOutput


class TestLlamaPDFParser:
    @pytest.fixture
    def parser(self):
        return LlamaPDFParser()

    def test_init(self, parser):
        """
        Test the initialization of the LlamaPDFParser class.
        """
        assert parser.initialized is False

    def test_load_documents_not_initialized(self, parser):
        """
        Test the load_documents method when the parser is not initialized.
        """
        with pytest.raises(
            ValueError, match="The Docling Parser has not been initialized."
        ):
            next(parser.load_documents(["test.pdf"]))

    @patch("os.path.exists", return_value=True)
    def test_load_documents_file_not_pdf(self, mock_exists, parser):
        """
        Test the load_documents method when the file is not a PDF file.
        """
        parser.initialized = True
        with pytest.raises(ValueError, match="The file test.txt must be a PDF file."):
            next(parser.load_documents(["test.txt"]))

    @patch("os.path.exists", return_value=False)
    def test_load_documents_file_not_found(self, mock_exists, parser):
        """
        Test the load_documents method when the file does not exist.
        """
        parser.initialized = True
        with pytest.raises(
            FileNotFoundError, match="The file test.pdf does not exist."
        ):
            next(parser.load_documents(["test.pdf"]))

    @patch("os.path.exists", return_value=True)
    def test_load_documents_success(self, mock_exists, parser):
        """
        Test the load_documents method when the parser is initialized and the file exists.
        """
        parser.initialized = True
        parser.converter = Mock()
        parser.converter.get_json_result.return_value = [{"test": "data"}]
        result = list(parser.load_documents(["test.pdf"]))
        assert result == [{"test": "data"}]

    @patch.object(LlamaPDFParser, "_LlamaPDFParser__initialize_llama")
    @patch.object(LlamaPDFParser, "load_documents")
    @patch.object(LlamaPDFParser, "_LlamaPDFParser__export_result")
    def test_parse_and_export(self, mock_export, mock_load, mock_init, parser):
        """
        Test the parse_and_export method by patching the load_documents and __export_result methods.
        """
        mock_load.return_value = [{"test": "data"}]
        mock_export.return_value = ParserOutput(text="test", tables=[], images=[])
        result = parser.parse_and_export("test.pdf")
        assert isinstance(result, list)
        assert isinstance(result[0], ParserOutput)
        mock_init.assert_called_once()
        mock_load.assert_called_once_with(["test.pdf"])
        mock_export.assert_called_once_with(
            {"test": "data"}, ["text", "tables", "images"]
        )

    def test_export_result(self, parser):
        """
        Test the __export_result method giving a json result with text, tables, and images that
        should be extracted.
        """
        json_result = {
            "pages": [
                {
                    "text": "Test text",
                    "items": [
                        {
                            "type": "table",
                            "md": "| Header |\n|--------|",
                            "csv": "Header\nValue",
                        }
                    ],
                }
            ]
        }
        with patch.object(
            LlamaPDFParser,
            "_extract_images",
            return_value=[{"image": Image.new("RGB", (60, 30))}],
        ):
            result = parser._LlamaPDFParser__export_result(
                json_result, ["text", "tables", "images"]
            )
        assert isinstance(result, ParserOutput)
        assert result.text == "Test text\n"
        assert len(result.tables) == 1
        assert len(result.images) == 1

    def test_extract_text(self):
        page = {"text": "Test text"}
        assert LlamaPDFParser._extract_text(page) == "Test text"

    def test_extract_tables(self):
        page = {
            "items": [
                {
                    "type": "table",
                    "md": "| Header |\n|--------|",
                    "csv": "Header\nValue",
                }
            ]
        }
        result = LlamaPDFParser._extract_tables(page)
        assert len(result) == 1
        assert result[0]["table_md"] == "| Header |\n|--------|"
        assert isinstance(result[0]["table_df"], pd.DataFrame)

    @patch("parseval.parsers.llama_parser.Image.open")
    @patch("os.remove")
    def test_extract_images(self, mock_remove, mock_image_open, parser):
        """
        Test the _extract_images method by patching the Image.open and os.remove functions.
        """
        page = {"dummy": "data"}
        parser.converter = Mock()
        parser.converter.get_images.return_value = [{"path": "test_image.jpg"}]
        mock_image_open.return_value.convert.return_value = Image.new("RGB", (60, 30))
        result = parser._extract_images(page)
        assert len(result) == 1
        assert isinstance(result[0]["image"], Image.Image)
        mock_remove.assert_called_once_with("test_image.jpg")
