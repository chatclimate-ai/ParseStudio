import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import fitz
from PIL import Image
import pandas as pd
from io import BytesIO
from parsestudio.parsers.pymupdf_parser import PyMuPDFParser, ParserOutput, TableElement, TextElement, ImageElement, Metadata


@pytest.fixture
def mock_page():
    mock = MagicMock(spec=fitz.Page)
    type(mock).parent = PropertyMock(return_value=MagicMock())
    mock.number = 1
    mock.get_text.return_value = "Sample text"
    mock.get_images.return_value = [
        (1, 0, 0, 0, 0, 0, 0, "image/jpeg", b"", "image1", 0)
    ]
    mock.find_tables.return_value = [
        MagicMock(
            to_markdown=lambda: "| Header |\n|--------|",
            to_pandas=lambda: pd.DataFrame({"Header": ["Value"]}),
        )
    ]
    mock.parent.extract_image.return_value = {"image": b"fake_image_data"}
    return mock


class TestPyMuPDFParser:
    @pytest.fixture
    def parser(self):
        return PyMuPDFParser()

    def test_init(self, parser):
        assert isinstance(parser, PyMuPDFParser)

    @patch("fitz.open")
    def test_load_documents(self, mock_open, parser):
        """
        Test that the parser loads documents correctly.
        """
        mock_doc = MagicMock()
        mock_doc.page_count = 2
        mock_doc.load_page.side_effect = [MagicMock(), MagicMock()]
        mock_open.return_value.__enter__.return_value = mock_doc

        pages = list(parser.load_documents(["test.pdf"]))
        assert len(pages) == 1  # One document
        assert len(pages[0]) == 2  # Two pages

    def test_parse_and_export_single_path(self, parser):
        """
        Test that the parser parses and exports a single document correctly.
        """
        with patch.object(PyMuPDFParser, "load_documents") as mock_load:
            mock_load.return_value = [[MagicMock()]]
            with patch.object(
                PyMuPDFParser, "_PyMuPDFParser__export_result"
            ) as mock_export:
                mock_export.return_value = ParserOutput(
                    text= TextElement(text="test")  
                )
                result = parser.parse("test.pdf")
                assert isinstance(result, list)
                assert len(result) == 1
                assert isinstance(result[0], ParserOutput)

    def test_parse_and_export_multiple_paths(self, parser):
        """
        Test that the parser parses and exports multiple documents correctly
        """
        with patch.object(PyMuPDFParser, "load_documents") as mock_load:
            mock_load.return_value = [[MagicMock()], [MagicMock()]]
            with patch.object(
                PyMuPDFParser, "_PyMuPDFParser__export_result"
            ) as mock_export:
                mock_export.return_value = ParserOutput(
                    text= TextElement(text="test") 
                )
                result = parser.parse(["test1.pdf", "test2.pdf"])
                assert isinstance(result, list)
                assert len(result) == 2
                assert all(isinstance(r, ParserOutput) for r in result)



    def test_export_result(self, parser, mock_page):
        """
        Test that the parser exports the result correctly.
        """
        with patch.object(PyMuPDFParser, "_extract_text") as mock_text:
            with patch.object(PyMuPDFParser, "_extract_tables") as mock_tables:
                with patch.object(PyMuPDFParser, "_extract_images") as mock_images:
                    mock_text.return_value = TextElement(text="Sample text")
                    mock_tables.return_value = [TableElement(
                        markdown="| Header |\n|--------|", 
                        dataframe=pd.DataFrame(), 
                        metadata=Metadata()
                        )]
                    
                    mock_images.return_value = [ImageElement(
                        image=Image.new("RGB", (60, 30)), 
                        metadata=Metadata()
                        )]

                    result = parser._PyMuPDFParser__export_result(
                        [mock_page], ["text", "tables", "images"]
                        )

                    assert isinstance(result, ParserOutput)
                    assert result.text.text == "Sample text\n"
                    assert len(result.tables) == 1
                    assert len(result.images) == 1

    def test_extract_text(self, mock_page):
        """
        Test that the parser extracts text correctly.
        """
        result = PyMuPDFParser._extract_text(mock_page)
        assert result.text == "Sample text"
        mock_page.get_text.assert_called_once_with("text")

    @patch("PIL.Image.open")
    def test_extract_images(self, mock_image_open, mock_page):
        """
        Test that the parser extracts images correctly.
        """
        mock_image_open.return_value.convert.return_value = Image.new("RGB", (60, 30))
        result = PyMuPDFParser._extract_images(mock_page)
        assert len(result) == 1
        assert isinstance(result[0].image, Image.Image)

    def test_extract_tables(self, mock_page):
        """
        Test that the parser extracts tables correctly.
        """
        result = PyMuPDFParser._extract_tables(mock_page)
        assert len(result) == 1
        assert isinstance(result[0].dataframe, pd.DataFrame)
