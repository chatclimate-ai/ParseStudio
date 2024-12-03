# ParseStudio Documentation


## Entry Point

The entry point for the `parsestudio` library is the PDFParser module, 
that acts as the main interface for the library. 

The PDFParser module initializes the parser and provides a method to parse a PDF file.
Which could be either:
- A DoclingParser
- A PymuPDFParser
- A LlmapParser

To run the parser, you can use the `run` method of the PDFParser module.

## Basic Usage

```python
from parsestudio.parse import PDFParser

parser = PDFParser(name="docling")
output = parser.run("path/to/pdf/file")
```

## Documentation

The `PDFParser` module is initialized with a parser `name` and its `parser_kwargs` as arguments. Note that the `parser_kwargs` are optional.
:::parsestudio.parse

The `run` method of the `PDFParser` module returns a `ParserOutput` object that contains the parsed data. Check the `ParserOutput` class in [Schemas](schemas.md) for more information.
