from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List
import pandas as pd
import PIL.Image as Image




class Metadata(BaseModel):
    """
    Metadata of the element.
    
    Attributes:
        page_number (int): The page number where the element is located.
        bbox (List[float]): Bounding box coordinates of the element.

    """
    page_number: int = Field(None, description="The page number where the element is located.")
    bbox: List[float] = Field(None, description="Bounding box coordinates of the element.")

    @field_validator("page_number")
    def validate_page_number(cls, page_number):
        if not isinstance(page_number, int):
            raise ValueError("The 'page_number' key must be an integer.")
        return page_number
    
    @field_validator("bbox")
    def validate_bbox(cls, bbox):
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(isinstance(i, float) for i in bbox):
            raise ValueError("The 'bbox' key must be a list of 4 floats.")
        return bbox


class TableElement(BaseModel):
    """
    Table element.
    
    Attributes:
        markdown (str): The markdown representation of the table.
        dataframe (pd.DataFrame): The pandas DataFrame representation of the table.
        metadata (Metadata): Metadata of the table.
    """
    markdown: str = Field(None, description="The markdown representation of the table.")
    dataframe: pd.DataFrame = Field(None, description="The pandas DataFrame representation of the table.")
    metadata: Metadata = Field(..., description="Metadata of the table.")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("markdown")
    def validate_table_md(cls, markdown):
        if markdown is not None and not isinstance(markdown, str):
            raise ValueError("The 'markdown' key must be a string.")
        return markdown
    
    @field_validator("dataframe")
    def validate_table_df(cls, dataframe):
        if dataframe is not None and not isinstance(dataframe, pd.DataFrame):
            raise ValueError("The 'dataframe' key must be a pandas DataFrame.")
        return dataframe

    @field_validator("metadata")
    def validate_table_metadata(cls, metadata):
        if metadata is not None and not isinstance(metadata, Metadata):
            raise ValueError("The 'metadata' key must be a TableMetadata object.")
        return metadata
    

class ImageElement(BaseModel):
    """
    Image element.

    Attributes:
        image (Image.Image): The image element.
        metadata (Metadata): Metadata of the image element.
    """
    image: Image.Image = Field(..., description="The image element.")
    metadata: Metadata = Field(..., description="Metadata of the image element.")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("image")
    def validate_image(cls, image):
        if not isinstance(image, Image.Image):
            raise ValueError("The 'image' key must be a PIL Image object.")
        return image

    @field_validator("metadata")
    def validate_metadata(cls, metadata):
        if metadata is not None and not isinstance(metadata, Metadata):
            raise ValueError("The 'metadata' key must be a Metadata object.")
        return metadata


class TextElement(BaseModel):
    """
    Text element.

    Attributes:
        text (str): The text element.
    """
    text: str = Field(..., description="The text element.")

    @field_validator("text")
    def validate_text(cls, text):
        if not isinstance(text, str):
            raise ValueError("The 'text' key must be a string.")
        return text

class ParserOutput(BaseModel):
    """
    Parser output.

    Attributes:
        text (TextElement): The text element.
        tables (List[TableElement]): List of table elements.
        images (List[ImageElement]): List of image elements.
    """
    text: TextElement = Field(None, description="The text element.")
    tables : List[TableElement] = Field(None, description="List of table elements.")
    images: List[ImageElement] = Field(None, description="List of image elements.")

    @field_validator("text")
    def validate_text_element(cls, text_element):
        if text_element is not None and not isinstance(text_element, TextElement):
            raise ValueError("The 'text_element' key must be a TextElement object.")
        return text_element

    @field_validator("tables")
    def validate_tables(cls, tables):
        if tables is not None and not all(isinstance(i, TableElement) for i in tables):
            raise ValueError("The 'tables' key must be a list of TableElement objects.")
        return tables
    
    @field_validator("images")
    def validate_images(cls, images):
        if images is not None and not all(isinstance(i, ImageElement) for i in images):
            raise ValueError("The 'images' key must be a list of ImageElement objects.")
        return images
