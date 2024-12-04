from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="parsestudio",
    version="1.0.3",
    author="Imene KOLLI",
    author_email="imene.kolli@df.uzh.ch",
    description="Parse PDF files using different parsers.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "docling>=2.5.2,<3.0.0",
        "pymupdf>=1.24.13,<2.0.0",
        "llama-parse>=0.5.14,<0.6.0",
        "pytest>=8.3.3,<9.0.0",
        "python-dotenv>=1.0.1,<2.0.0",
    ],
    python_requires=">=3.12,<3.13",
)
