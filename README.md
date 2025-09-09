<div align="center">

![ParseStudio Logo](./images/logo.webp)

# 📄 ParseStudio ✨

[![PyPI version](https://img.shields.io/pypi/v/parsestudio.svg)](https://pypi.org/project/parsestudio/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/chatclimate-ai/ParseStudio/blob/main/LICENSE)
[![Python versions](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/chatclimate-ai/ParseStudio.svg)](https://github.com/chatclimate-ai/ParseStudio/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/chatclimate-ai/ParseStudio.svg)](https://github.com/chatclimate-ai/ParseStudio/issues)
[![GitHub forks](https://img.shields.io/github/forks/chatclimate-ai/ParseStudio.svg)](https://github.com/chatclimate-ai/ParseStudio/network)
[![Downloads](https://static.pepy.tech/badge/parsestudio)](https://pepy.tech/project/parsestudio)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

</div>

**ParseStudio** is a powerful and flexible Python library for extracting and parsing content from PDF documents. It provides an intuitive interface for handling diverse tasks such as extracting text, tables, and images using different parsing backends.

## Requirements

- Python 3.11 or higher
- Compatible with Python 3.11, 3.12

---

## Key Features

- **Modular Design**: Choose between multiple parser backends (Docling, PymuPDF, Llama Parse, Anthropic Claude, OpenAI GPT-4 Vision) to suit your needs.
- **Multimodal Parsing**: Extract text, tables, and images seamlessly.
- **Extensible**: Easily adjust parsing behavior with additional parameters.

---

## 🚀 Installation

### Via pip (recommended)

```bash
pip install parsestudio
```

### From source

```bash
git clone https://github.com/chatclimate-ai/ParseStudio.git
cd ParseStudio
pip install .
```

### Development installation

```bash
git clone https://github.com/chatclimate-ai/ParseStudio.git
cd ParseStudio
pip install -e ".[dev]"
```

## ⚡ Quick Start

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
  - Uses OpenAI's file search with vector embeddings for efficient PDF processing
  - Automatically handles text extraction and table detection
  - More efficient, cheaper, and faster than image-based approaches

## Contributing

We welcome contributions from the community! ParseStudio uses modern development tools to ensure code quality.

### Quick Development Setup

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/chatclimate-ai/ParseStudio.git
cd ParseStudio
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install

# Verify setup
make all-checks
```

### Development Commands

```bash
make format     # Format code with Black & isort
make lint       # Run ruff linter
make type-check # Run mypy type checker  
make test       # Run tests
make all-checks # Run all quality checks
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/chatclimate-ai/ParseStudio/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/chatclimate-ai/ParseStudio/discussions)
- 📧 **Contact**: For questions about usage or contributions, please open an issue

## Acknowledgments

ParseStudio integrates with several excellent open-source and commercial parsing solutions:
- [Docling](https://github.com/DS4SD/docling) - Advanced document parsing
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - Fast PDF processing
- [LlamaParse](https://github.com/run-llama/llama_parse) - AI-powered document parsing
- [Anthropic Claude](https://www.anthropic.com/claude) - Advanced AI capabilities
- [OpenAI GPT-4](https://openai.com/gpt-4) - State-of-the-art document analysis
