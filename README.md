# ParserStudio

Parsestudio is a powerful Python library for extracting and parsing content from PDF documents. It provides an intuitive interface for handling diverse tasks such as extracting text, tables, and images using different parsing backends.

---

## Key Features

- **Modular Design**: Choose between multiple parser backends (DoclingParser, PymuPDFParser, LlmapParser) to suit your needs.
- **Multimodal Parsing**: Extract text, tables, and images seamlessly.
- **Extensible**: Easily integrate custom parsers or adjust parsing behavior with additional parameters.

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
from parsestudio import PDFParser

# Initialize with the desired parser backend
parser = PDFParser(parser="docling")  # Options: "docling", "pymupdf", "llama"
```

### 2. Parse a PDF File

```python
outputs = parser.run("path/to/file.pdf", modalities=["text", "tables", "images"])

# Access text content
print(outputs[0].text)

# Access tables
for table in outputs[0].tables:
    print(table.markdown)

# Access images
for image in outputs[0].images:
    image.image.show()
```

### 3. Supported Parsers

Choose from the following parsers based on your requirements:
- **[Docling](https://github.com/DS4SD/docling)**: Advanced parser for extracting rich content.
- **[PyMuPDF](https://github.com/pymupdf/PyMuPDF)**: Lightweight and efficient.
- **[LlamaParse](https://github.com/run-llama/llama_parse)**: AI-enhanced parser with advanced capabilities.

Each parser has its own strengths. Choose the one that best fits your use case.

##### LlamaPDFParser Setup

If you choose to use the LlmapParser, you need to set up an API key. Follow these steps:

1. Create a `.env` File: In the root directory of your project, create a file named `.env`.
2. Add Your API Key: Add the following line to the .env file, replacing your-api-key with your Llmap API key:
    ```bash
   LLAMA_API_KEY=your-api-key
   ```

