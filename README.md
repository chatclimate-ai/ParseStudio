# ParserStudio

Parsestudio is a powerful Python library for extracting and parsing content from PDF documents. It provides an intuitive interface for handling diverse tasks such as extracting text, tables, and images using different parsing backends.

---

## Key Features

- **Modular Design**: Choose between multiple parser backends (Docling, PymuPDF, Llama Parse, Anthropic Claude, OpenAI GPT-4 Vision) to suit your needs.
- **Multimodal Parsing**: Extract text, tables, and images seamlessly.
- **Extensible**: Easily adjust parsing behavior with additional parameters.

---

## Installation

Get started with Parsestudio by installing it via pip:

```bash
pip install parsestudio
```

Install the library from source by cloning the repository and running:

```bash
git clone https://github.com/chatclimate-ai/ParseStudio.git
cd ParseStudio
pip install .
```

## Quick Start


### 1. Import and Initialize the Parser

```python
from parsestudio.parse import PDFParser

# Initialize with the desired parser backend
parser = PDFParser(parser="docling")  # Options: "docling", "pymupdf", "llama", "anthropic", "openai"
```

### 2. Parse a PDF File

```python
outputs = parser.run(["path/to/file.pdf"], modalities=["text", "tables", "images"])

# Access text content
print(outputs[0].text)
# Output: text="This is the extracted text content from the PDF file."

# Access tables
for table in outputs[0].tables:
    print(table.markdown)
# Output: | Header 1 | Header 2 |
#         |----------|----------|
#         | Value 1  | Value 2  |

# Access images
for image in outputs[0].images:
    image.image.show()
    metadata = image.metadata
    print(metadata)

# Output: Metadata(page_number=1, bbox=[0, 0, 100, 100])
```

### 3. Supported Parsers

Choose from the following parsers based on your requirements:
- **[Docling](https://github.com/DS4SD/docling)**: Advanced parser with multimodal capabilities.
- **[PyMuPDF](https://github.com/pymupdf/PyMuPDF)**: Lightweight and efficient.
- **[LlamaParse](https://github.com/run-llama/llama_parse)**: AI-enhanced parser with advanced capabilities.
- **[Anthropic Claude](https://www.anthropic.com/claude)**: Advanced AI model using Claude 3.5 Sonnet with native PDF processing capabilities.
- **[OpenAI GPT-4 Vision](https://openai.com/gpt-4)**: State-of-the-art vision model for document analysis.

Each parser has its own strengths. Choose the one that best fits your use case.

##### API Key Setup

If you choose to use the Llama, Anthropic, or OpenAI parsers, you need to set up API keys. Follow these steps:

1. Create a `.env` File: In the root directory of your project, create a file named `.env`.
2. Add Your API Keys: Add the following lines to the .env file, replacing the placeholders with your actual API keys:
   ```
   LLAMA_API_KEY=your-llama-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   OPENAI_API_KEY=your-openai-api-key
   ```

##### Parser-Specific Requirements

- **Llama Parser**: Requires a Llama API key
- **Anthropic Parser**: 
  - Requires an Anthropic API key
  - Uses Claude 3.5 Sonnet with native PDF processing (no image conversion needed)
  - Supports text and table extraction
  - Note: Image extraction not currently supported due to API limitations
- **OpenAI Parser**: 
  - Requires an OpenAI API key
  - Uses GPT-4 Vision for document analysis
  - Requires `pdf2image` and `poppler` for PDF processing
  - Install poppler:
    - Windows: Download from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases/)
    - Linux: `sudo apt-get install poppler-utils`
    - Mac: `brew install poppler`

## Contributing

We welcome contributions from the community! To contribute to Parsestudio, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push your changes to your fork.
5. Open a pull request.
6. Our team will review your changes and merge them if they meet our guidelines.

Congratulations! You've contributed to Parsestudio.

