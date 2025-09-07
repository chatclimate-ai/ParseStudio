import pytest
import json
from parsestudio.parsers.openai_parser import OpenAIPDFParser, ParserOutput, TableElement, TextElement, ImageElement, Metadata
import pandas as pd
from PIL import Image
import io
import base64
import os

class TestOpenAIPDFParser:
    @pytest.fixture
    def parser(self):
        return OpenAIPDFParser()

    def test_init(self):
        openai_options = {"max_output_tokens": 2048, "model": "gpt-4o-mini"}
        parser = OpenAIPDFParser(openai_options)
        expected_options = {"model": "gpt-4o-mini", "max_output_tokens": 2048, "temperature": 0}
        assert parser.options == expected_options
        assert parser.client is not None

    def test_get_image_uri(self, parser):
        # Create a test image
        test_image = Image.new('RGB', (100, 100), color='red')
        
        # Get the URI using the module-level function
        from parsestudio.parsers.openai_parser import _b64_image_uri
        uri = _b64_image_uri(test_image)
        
        # Verify the URI format
        assert uri.startswith('data:image/png;base64,')
        
        # Decode and verify the image data
        base64_data = uri.split(',')[1]
        decoded_data = base64.b64decode(base64_data)
        decoded_image = Image.open(io.BytesIO(decoded_data))
        
        assert decoded_image.size == (100, 100)

    @pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
    def test_analyze_page(self, parser):
        # Create a simple test image with some text-like pattern
        test_image = Image.new('RGB', (200, 100), color='white')
        
        # Test the method with real API call
        result = parser._analyze_page(test_image, page_number=1)
        
        # Verify the result structure
        assert "text_content" in result
        assert "tables" in result
        assert isinstance(result["text_content"], str)
        assert isinstance(result["tables"], list)

    @pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set") 
    def test_load_documents_structure(self, parser):
        # Test with a non-existent file to check error handling
        result = list(parser.load_documents(["nonexistent.pdf"]))
        
        # Should return one empty result due to error handling
        assert len(result) == 1
        assert result[0]["text_content"] == ""
        assert result[0]["tables"] == []

    def test_validate_modalities(self, parser):
        parser._validate_modalities(["text", "tables", "images"])
        with pytest.raises(ValueError):
            parser._validate_modalities(["invalid"])

    def test_parse_structure(self, parser):
        # Test parse method structure without real file
        result = parser.parse("nonexistent.pdf", ["text", "tables"])
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ParserOutput)
        assert hasattr(result[0], 'text')
        assert hasattr(result[0], 'tables') 
        assert hasattr(result[0], 'images')

    def test_extract_tables(self, parser):
        table_data = "| Header |\n|--------|\n| Value |"
        parsed_data = {
            "tables": [{
                "markdown": table_data,
                "page_number": 1,
                "bbox": [0, 0, 100, 100]
            }]
        }
        result = parser._extract_tables(parsed_data)
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TableElement)
        assert result[0].markdown == table_data
        assert isinstance(result[0].dataframe, pd.DataFrame)
        assert result[0].metadata.page_number == 1
        assert result[0].metadata.bbox == [0, 0, 100, 100]
