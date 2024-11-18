from parseval.parse import PDFParser

if __name__ == "__main__":
    parser = PDFParser(parser="pymupdf")
    out = parser.run(pdf_path="data/adobe/adobe.pdf", modalities=["text"])
    print(out[0].text[:200])

    ## All good
