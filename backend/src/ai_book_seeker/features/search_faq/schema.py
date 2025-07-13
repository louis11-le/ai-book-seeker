from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class FAQSchema(BaseModel):
    """
    Input schema for FAQ tool. Validates that 'query' is a non-empty, stripped string.
    """

    query: str

    @field_validator("query", mode="after")
    @classmethod
    def query_must_be_non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("'query' must be a non-empty string.")
        return v


class FAQAnswer(BaseModel):
    """
    Output schema for a single FAQ answer.
    """

    category: str
    question: str
    answer: str
    similarity: Optional[float] = Field(None, description="Optional similarity score")


class FAQOutputSchema(BaseModel):
    """
    Output schema for the FAQ tool. Contains the answer text and a list of FAQAnswer objects.
    """

    text: str
    data: List[FAQAnswer]
