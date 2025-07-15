from typing import List, Optional

from pydantic import BaseModel, Field


class BookRecommendationSchema(BaseModel):
    """
    Schema for the get_book_recommendation tool.

    Attributes:
        age (Optional[int]): The age of the reader (single value, for backward compatibility).
        age_from (Optional[int]): The starting age if a range or comparison is specified.
        age_to (Optional[int]): The ending age if a range or comparison is specified.
        purpose (Optional[str]): The purpose of the book (learning, entertainment).
        budget (Optional[float]): The budget for buying books.
        genre (Optional[str]): The preferred genre (optional).
    """

    age: Optional[int] = Field(None, description="The age of the reader (single value, for backward compatibility)")
    age_from: Optional[int] = Field(None, description="The starting age if a range or comparison is specified")
    age_to: Optional[int] = Field(None, description="The ending age if a range or comparison is specified")
    purpose: Optional[str] = Field(None, description="The purpose of the book (learning, entertainment)")
    budget: Optional[float] = Field(None, description="The budget for buying books")
    genre: Optional[str] = Field(None, description="The preferred genre (optional)")


class BookRecommendation(BaseModel):
    """
    Output schema for a single recommended book.
    """

    id: int
    title: str
    author: str
    description: Optional[str] = ""
    from_age: Optional[int] = None
    to_age: Optional[int] = None
    purpose: Optional[str] = ""
    genre: Optional[str] = ""
    price: float = 0.0
    tags: List[str] = []
    quantity: int = 0
    reason: Optional[str] = None


class BookRecommendationOutputSchema(BaseModel):
    """
    Output schema for the Book Recommendation tool. Contains a summary text and a list of recommended books.
    """

    text: str
    data: List[BookRecommendation]
