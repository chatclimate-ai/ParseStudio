import pytest
import json
from parsestudio.parsers.openai_parser import OpenAIPDFParser
from parsestudio.parsers.schemas import ParserOutput, TableElement, TextElement, ImageElement, Metadata
from parsestudio.parsers.openai_file_search_parser import OpenAIFileSearchPDFParser
import pandas as pd
import os

class TestOpenAIPDFParser:
    @pytest.fixture  
    def parser(self):
        return OpenAIPDFParser()

    def test_init_default(self):
        parser = OpenAIPDFParser()
        assert isinstance(parser.parser, OpenAIFileSearchPDFParser)

    def test_init_with_options(self):
        openai_options = {"max_tokens": 2048, "model": "gpt-4o-mini"}
        parser = OpenAIPDFParser(openai_options=openai_options)
        assert isinstance(parser.parser, OpenAIFileSearchPDFParser)
        assert parser.parser.options["max_tokens"] == 2048
        assert parser.parser.options["model"] == "gpt-4o-mini"

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
        result = parser.parser._extract_tables(parsed_data)
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TableElement)
        assert result[0].markdown == table_data
        assert isinstance(result[0].dataframe, pd.DataFrame)
        assert result[0].metadata.page_number == 1
        assert result[0].metadata.bbox == [0, 0, 100, 100]
