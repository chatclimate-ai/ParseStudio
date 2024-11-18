from pydantic import BaseModel, Field, field_validator
from typing import List, Dict
import pandas as pd
from PIL import Image


class ParserOutput(BaseModel):
    text: str = Field(..., description="The parsed text from the document.")
    tables: List[Dict] = Field(..., description="The parsed tables from the document.")
    images: List[Dict] = Field(..., description="The parsed images from the document.")

    @field_validator("text")
    def validate_text(cls, text):
        if not isinstance(text, str):
            raise ValueError("The 'text' key must be a string.")
        return text

    @field_validator("tables")
    def validate_tables(cls, tables):
        if not isinstance(tables, list):
            raise ValueError("The 'tables' key must be a list.")

        if not tables:
            return tables

        for table in tables:
            if not isinstance(table, dict):
                raise ValueError("Each table must be a dictionary.")
            if "table_md" not in table or not isinstance(table["table_md"], str):
                raise ValueError("Each table must have a 'table_md' key of type str.")

            if "table_df" in table and not isinstance(table["table_df"], pd.DataFrame):
                raise ValueError(
                    "Each table that has a 'table_df' key must be a pandas DataFrame."
                )

        return tables

    @field_validator("images")
    def validate_images(cls, images):
        if not isinstance(images, list):
            raise ValueError("The 'images' key must be a list.")

        if not images:
            return images

        for image in images:
            if not isinstance(image, dict):
                raise ValueError("Each image must be a dictionary.")

            if "image" not in image or not isinstance(image["image"], Image.Image):
                raise ValueError(
                    "Each image must have an 'image' key of type PIL Image."
                )
        return images
