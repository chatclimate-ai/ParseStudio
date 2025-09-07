from typing import Union, List, Dict, Optional, Any, Literal
from .openai_vision_parser import OpenAIVisionPDFParser
from .openai_file_search_parser import OpenAIFileSearchPDFParser
from .schemas import ParserOutput

class OpenAIPDFParser:
    """
    Unified OpenAI PDF Parser that supports two approaches:
    - 'vision': Uses GPT-4 Vision to analyze PDF pages converted to images
    - 'file_search': Uses OpenAI's file search with vector embeddings
    
    Args:
        approach: Either 'vision' or 'file_search'
        openai_options: Options to pass to the underlying parser
    """
    
    def __init__(
        self,
        approach: Literal["vision", "file_search"] = "file_search",
        openai_options: Optional[Dict[str, Any]] = None
    ):
        self.approach = approach
        
        if approach == "vision":
            self.parser = OpenAIVisionPDFParser(openai_options)
        elif approach == "file_search":
            self.parser = OpenAIFileSearchPDFParser(openai_options)
        else:
            raise ValueError(f"Invalid approach: '{approach}'. Valid options are: 'vision', 'file_search'")
    
    def parse(
        self,
        paths: Union[str, List[str]], 
        modalities: List[str] = ["text", "tables", "images"],
        **kwargs
    ) -> List[ParserOutput]:
        """
        Parse PDF files using the selected OpenAI approach.
        
        Args:
            paths: Path or list of paths to PDF files
            modalities: List of modalities to extract
            **kwargs: Additional arguments passed to the underlying parser
            
        Returns:
            List of ParserOutput objects
        """
        return self.parser.parse(paths, modalities, **kwargs)
    
    def load_documents(self, paths: List[str]):
        """Load documents using the selected parser approach."""
        return self.parser.load_documents(paths)
    
    def _validate_modalities(self, modalities: List[str]) -> None:
        """Validate modalities using the selected parser."""
        return self.parser._validate_modalities(modalities)