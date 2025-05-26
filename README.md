# ParserStudio

Parsestudio is a powerful Python library for extracting and parsing content from PDF documents. It provides an intuitive interface for handling diverse tasks such as extracting text, tables, and images using different parsing backends.

---

## Key Features

- **Modular Design**: Choose between multiple parser backends (Docling, PymuPDF, Llama Parse) to suit your needs.
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
parser = PDFParser(parser="docling")  # Options: "docling", "pymupdf", "llama"
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

Each parser has its own strengths. Choose the one that best fits your use case.

##### Llama Setup

If you choose to use the LlamaPDFParser, you need to set up an API key. Follow these steps:

1. Create a `.env` File: In the root directory of your project, create a file named `.env`.
2. Add Your API Key: Add the following line to the .env file, replacing your-api-key with your Llmap API key: `LLAMA_API_KEY=your-api-key`

## Contributing

We welcome contributions from the community! To contribute to Parsestudio, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push your changes to your fork.
5. Open a pull request.
6. Our team will review your changes and merge them if they meet our guidelines.

Congratulations! You've contributed to Parsestudio.

---

### Local File Conversion (`convert_files.py`)

This script allows for local batch processing of PDF files to extract text, tables, and images. It monitors an `input` directory, processes new PDFs found there, saves the extracted content into an `output` directory, and moves processed PDFs to an archive folder.

**Purpose:**
To provide a convenient way to extract data from multiple PDF files locally using the `parsestudio` library's capabilities.

**Prerequisites:**
*   **Python 3.x:** Ensure you have Python installed.
*   **Dependencies:** Install all necessary dependencies by running the following command from the root of the project:
    ```bash
    pip install -r requirements.txt
    ```

**Setup:**
*   **`input/` folder:** Place the PDF files you want to process into the `input` directory at the root of the project.
*   **`output/` folder:** Extracted content will be saved in subdirectories within the `output` directory (automatically created if it doesn't exist). Each processed PDF will have its own subdirectory in `output/`, named after the original PDF file (e.g., content from `mydoc.pdf` will be in `output/mydoc/`).
*   **`input/processed/` folder:** Successfully processed PDFs will be moved from the `input/` directory to the `input/processed/` directory. This helps in keeping track of which files have been processed.

**Running the Script:**
To start the conversion process, navigate to the root of the project in your terminal and run:
```bash
python convert_files.py
```
The script will scan the `input` directory for PDF files, process them, and save their outputs.

**Output Structure:**
For each processed PDF file (e.g., `example.pdf`), a corresponding subdirectory (e.g., `output/example/`) will be created. Inside this subdirectory, you can expect to find:
*   `text_content.txt`: Contains all extracted text from the PDF.
*   `table_N.md`: Markdown files for each table extracted (e.g., `table_1.md`, `table_2.md`).
*   `image_N.png`: Image files for each image extracted (e.g., `image_1.png`, `image_2.png`).

If a PDF cannot be processed, an error message will be displayed, and the PDF will remain in the `input` directory.

