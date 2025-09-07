# The Anthropic Parser

The Anthropic parser uses Anthropic's Claude 3.5 Sonnet model with native PDF processing capabilities to parse PDFs and extract text and tables. It leverages Claude's advanced document understanding without requiring image conversion.

## Key Features

- **Native PDF Processing**: Direct PDF analysis without conversion to images
- **Advanced Text Extraction**: High-quality text extraction using Claude 3.5 Sonnet
- **Table Detection**: Automatic table extraction and conversion to markdown/DataFrame format
- **API Key Authentication**: Secure authentication using Anthropic API keys

## Limitations

- **Image Extraction**: Currently not supported due to API limitations
- **API Costs**: Uses Anthropic's paid API service
- **Rate Limits**: Subject to Anthropic's API rate limiting

## Documentation
:::parsestudio.parsers.anthropic_parser
