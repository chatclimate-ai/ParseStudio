# Parstudio Documentation


## Entry Point

The entry point for the Parstudio library is the PDFParser module, 
that acts as the main interface for the library. 

The PDFParser module initializes the parser and provides a method to parse a PDF file.
Which could be either:
- A DoclingParser
- A PymuPDFParser
- A LlmapParser

To run the parser, you can use the `run` method of the PDFParser module.

## Documentation
:::parstudio.parse
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
