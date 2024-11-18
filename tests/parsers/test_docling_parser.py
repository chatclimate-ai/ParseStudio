import pytest
from unittest.mock import Mock, patch
from parstudio.parsers.docling_parser import DoclingPDFParser, ParserOutput
from docling.datamodel.document import ConversionResult, DoclingDocument
from docling.datamodel.base_models import ConversionStatus
from PIL import Image
import pandas as pd


class TestDoclingPDFParser:
    @pytest.fixture
    def parser(self):
        return DoclingPDFParser()

    def test_init(self, parser):
        assert parser.embed_images is None
        assert parser.initialized is False

    @pytest.mark.parametrize("initialized", [True, False])
    def test_load_documents(self, parser, initialized):
        parser.initialized = initialized
        if not initialized:
            with pytest.raises(ValueError):
                next(parser.load_documents(["test.pdf"]))
        else:
            parser.converter = Mock()
            parser.converter.convert_all.return_value = [Mock(spec=ConversionResult)]
            result = next(parser.load_documents(["test.pdf"]))
            assert isinstance(result, ConversionResult)

    @patch(
        "parstudio.parsers.docling_parser.DoclingPDFParser._DoclingPDFParser__initialize_docling"
    )
    @patch("parstudio.parsers.docling_parser.DoclingPDFParser.load_documents")
    def test_parse_and_export(self, mock_load_documents, mock_initialize, parser):
        # Create a mock ConversionResult
        mock_document = Mock(spec=DoclingDocument)
        mock_result = Mock(spec=ConversionResult)
        mock_result.status = ConversionStatus.SUCCESS
        mock_result.document = mock_document

        # Make load_documents return an iterable (list) containing the mock result
        mock_load_documents.return_value = [mock_result]

        # Create a mock ParserOutput with default values
        mock_parser_output = ParserOutput(
            text="Sample text",
            tables=[{"table_md": "| Header |\n|--------|", "table_df": pd.DataFrame()}],
            images=[{"image": Image.new("RGB", (60, 30), color="red")}],
        )

        # Mock __export_result to return the mock ParserOutput object
        with patch.object(
            parser, "_DoclingPDFParser__export_result", return_value=mock_parser_output
        ):
            result = parser.parse_and_export("test.pdf")

        # Assert that load_documents was called
        mock_load_documents.assert_called_once_with(["test.pdf"])

        # Assert that the result is a list containing a ParserOutput object
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ParserOutput)

    def test_extract_tables(self):
        mock_table_item = Mock()
        mock_table_item.export_to_markdown.return_value = "| Header |\n|--------|"
        mock_table_item.export_to_dataframe.return_value = Mock()

        result = DoclingPDFParser._extract_tables(mock_table_item)
        assert isinstance(result, list)
        assert "table_md" in result[0]
        assert "table_df" in result[0]

    def test_extract_images(self):
        mock_picture_item = Mock()
        mock_picture_item.image.pil_image = Mock()

        result = DoclingPDFParser._extract_images(mock_picture_item)
        assert isinstance(result, list)
        assert "image" in result[0]

    def test_extract_text(self, parser):
        mock_document = Mock(spec=DoclingDocument)
        mock_document.export_to_markdown.return_value = "Sample text"

        result = parser._extract_text(mock_document)
        assert isinstance(result, str)
        assert result == "Sample text"
