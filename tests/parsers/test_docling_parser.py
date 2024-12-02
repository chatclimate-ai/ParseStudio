import pytest
from unittest.mock import Mock, patch
from parsestudio.parsers.docling_parser import DoclingPDFParser, ParserOutput, TableElement, TextElement, ImageElement, Metadata
from docling.datamodel.document import ConversionResult, DoclingDocument
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.types.doc import TableItem, PictureItem
from PIL import Image
import pandas as pd
import sys


class TestDoclingPDFParser:
    @pytest.fixture
    def parser(self):
        return DoclingPDFParser()

    def test_init(self, parser):
        pipeline_options = PdfPipelineOptions(do_ocr=False)
        parser = DoclingPDFParser(pipeline_options=pipeline_options)
        assert parser.converter.format_to_options[InputFormat.PDF].pipeline_options == pipeline_options
        assert parser.converter.format_to_options[InputFormat.PDF].pipeline_options.do_ocr is False

    
    def test_load_documents(self, parser):
        parser.converter = Mock()
        parser.converter.convert_all.return_value = [Mock(spec=ConversionResult)]
        result = next(parser.load_documents(["test.pdf"]))
        assert isinstance(result, ConversionResult)

    def test_validate_modalities(self, parser):
        # Test with valid modalities
        try:
            parser._validate_modalities(["text", "tables", "images"])
        except ValueError:
            pytest.fail("Valid modalities raised ValueError unexpectedly")

        # Test with an invalid modality
        with pytest.raises(ValueError):
            parser._validate_modalities(["text", "invalid_modality"])

  
    @patch("parsestudio.parsers.docling_parser.DoclingPDFParser.load_documents")
    def test_parse(self, mock_load_documents, parser):
        mock_result = Mock(spec=ConversionResult)
        mock_result.status = ConversionStatus.SUCCESS
        mock_result.document = Mock(spec=DoclingDocument)

       
        mock_load_documents.return_value = [mock_result]

        mock_parser_output = ParserOutput(
            text= TextElement(text="Sample text"),
            tables=[TableElement(
                markdown="| Header |\n|--------|", 
                dataframe=pd.DataFrame(),
                metadata= Metadata()
                )],
            images=[ImageElement(
                image=Image.new("RGB", (60, 30), color="red"),
                metadata= Metadata()
                )]
        )

        # Mock __export_result to return the mock ParserOutput object
        with patch.object(
            parser, "_DoclingPDFParser__export_result", return_value=mock_parser_output
        ):
            result = parser.parse("test.pdf")

        mock_load_documents.assert_called_once_with(
            ["test.pdf"],
            True,
            sys.maxsize,
            sys.maxsize
        )

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ParserOutput)

    def test_extract_tables(self):
        mock_table_item = Mock(spec=TableItem)
        mock_table_item.export_to_markdown.return_value = "| Header |\n|--------|"
        mock_table_item.export_to_dataframe.return_value = pd.DataFrame([[1, 2], [3, 4]])
        mock_table_item.prov = [Mock(page_no=1, bbox=Mock(l=0, t=0, r=1, b=1))]


        result = DoclingPDFParser._extract_tables(mock_table_item)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TableElement)

        assert result[0].markdown == "| Header |\n|--------|"
        assert result[0].dataframe.shape == (2, 2)
        assert result[0].metadata.page_number == 1
        assert result[0].metadata.bbox == [0.0, 0.0, 1.0, 1.0]

    def test_extract_images(self):
        mock_picture_item = Mock(spec=PictureItem)
        mock_image = Image.new("RGB", (60, 30), color="red")
        mock_picture_item.get_image.return_value = mock_image
        mock_picture_item.prov = [Mock(page_no=1, bbox=Mock(l=0, t=0, r=1, b=1))]

        result = DoclingPDFParser._extract_images(mock_picture_item, Mock(spec=DoclingDocument))

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ImageElement)

        assert result[0].image.size == (60, 30)
        assert isinstance(result[0].metadata, Metadata)
        assert result[0].metadata.page_number == 1
        assert result[0].metadata.bbox == [0.0, 0.0, 1.0, 1.0]

    def test_extract_images_no_image(self, parser):
        # Create a mock PictureItem
        mock_picture_item = Mock(spec=PictureItem)
        
        # Define mock return value for get_image as None
        mock_picture_item.get_image.return_value = None
        
        # Call the method to test
        result = DoclingPDFParser._extract_images(mock_picture_item, Mock(spec=DoclingDocument))

        # Assert the result is an empty list
        assert result == []


    def test_extract_text(self, parser):
        mock_document = Mock(spec=DoclingDocument)
        mock_document.export_to_markdown.return_value = "Sample text"

        result = parser._extract_text(mock_document, {})

        assert isinstance(result, TextElement)
        assert result.text == "Sample text"

    def test_extract_text_with_options(self, parser):
        mock_document = Mock(spec=DoclingDocument)
        mock_document.export_to_markdown.return_value = "Sample text"
        markdown_options = {"option1": "value1", "option2": "value2"}

        result = parser._extract_text(mock_document, markdown_options)

        mock_document.export_to_markdown.assert_called_once_with(**markdown_options)

        assert isinstance(result, TextElement)
        assert result.text == "Sample text"
    
