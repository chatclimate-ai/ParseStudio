from typing import Union, List, Dict, Optional, Any
from .openai_file_search_parser import OpenAIFileSearchPDFParser
from .schemas import ParserOutput

class OpenAIPDFParser:
    """
    OpenAI PDF Parser using file search approach.
    Uses OpenAI's file search with vector embeddings for efficient PDF processing.
    
    Args:
        openai_options: Options to pass to the underlying parser
    """
    
    def __init__(
        self,
        openai_options: Optional[Dict[str, Any]] = None
    ):
        self.parser = OpenAIFileSearchPDFParser(openai_options)
    
    def parse(
        self,
        paths: Union[str, List[str]], 
        modalities: List[str] = ["text", "tables", "images"],
        **kwargs
    ) -> List[ParserOutput]:
        """
        Parse PDF files using OpenAI's file search approach.
        
        Args:
            paths: Path or list of paths to PDF files
            modalities: List of modalities to extract
            **kwargs: Additional arguments passed to the underlying parser
            
        Returns:
            List of ParserOutput objects
        """
        return self.parser.parse(paths, modalities, **kwargs)
    
    def load_documents(self, paths: List[str]):
        """Load documents using the file search parser."""
        return self.parser.load_documents(paths)
    
    def _validate_modalities(self, modalities: List[str]) -> None:
        """Validate modalities using the parser."""
        return self.parser._validate_modalities(modalities)