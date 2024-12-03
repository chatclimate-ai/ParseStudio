# Parstudio Documentation


## Entry Point

The entry point for the `parsestudio` library is the PDFParser module, 
that acts as the main interface for the library. 

The PDFParser module initializes the parser and provides a method to parse a PDF file.
Which could be either:
- A DoclingParser
- A PymuPDFParser
- A LlmapParser

To run the parser, you can use the `run` method of the PDFParser module.

## Documentation

The `PDFParser` module is initialized with a parser `name` and its `parser_kwargs` as arguments. Note that the `parser_kwargs` are optional.
:::parsestudio.parse
    rendering:
        show_root_heading: true
        show_source: true
        show_sources: true
        show_source_type: true
        show_methods: true
        show_class_attributes: true
        show_class_parameters: true
        show_object_attributes: true
        show_object_parameters: true
        show_inherited_methods: true

The `run` method of the `PDFParser` module returns a `ParserOutput` object that contains the parsed data. A `ParserOutput` object has the following attributes
