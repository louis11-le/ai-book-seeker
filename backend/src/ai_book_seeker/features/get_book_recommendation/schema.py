import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class BaseBookRecommendationCriteria(BaseModel):
    """
    Base schema for book recommendation criteria with common fields.

    This base schema contains the common fields used across different
    book recommendation contexts (tool input, service logic, intent categorization).
    """

    age: Optional[int] = Field(
        None, ge=0, le=120, description="The age of the reader (single value, for backward compatibility)"
    )
    age_from: Optional[int] = Field(
        None, ge=0, le=120, description="The starting age if a range or comparison is specified"
    )
    age_to: Optional[int] = Field(
        None, ge=0, le=120, description="The ending age if a range or comparison is specified"
    )
    purpose: Optional[str] = Field(None, description="The purpose of the book (learning, entertainment)")
    budget: Optional[float] = Field(None, ge=0.0, description="The budget for buying books")
    genre: Optional[str] = Field(None, description="The preferred genre (optional)")

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: Optional[str]) -> Optional[str]:
        """Convert empty strings to None for purpose field."""
        if v == "":
            return None
        return v

    @field_validator("genre")
    @classmethod
    def validate_genre(cls, v: Optional[str]) -> Optional[str]:
        """Convert empty strings to None for genre field."""
        if v == "":
            return None
        return v

    @field_validator("age_to")
    @classmethod
    def validate_age_range(cls, v: Optional[int], info) -> Optional[int]:
        """Validate that age_to >= age_from when both are provided."""
        if v is not None and info.data.get("age_from") is not None:
            if v < info.data["age_from"]:
                raise ValueError("age_to must be greater than or equal to age_from")
        return v

    @field_validator("age", "age_from", "age_to")
    @classmethod
    def validate_mutual_exclusivity(cls, v: Optional[int], info) -> Optional[int]:
        """Validate that age and age_from/age_to are not used together."""
        if v is not None:
            if info.field_name == "age" and (info.data.get("age_from") or info.data.get("age_to")):
                raise ValueError("Cannot specify both 'age' and 'age_from'/'age_to'")
            elif info.field_name in ["age_from", "age_to"] and info.data.get("age"):
                raise ValueError("Cannot specify both 'age' and 'age_from'/'age_to'")
        return v

    @field_validator("age", "age_from", "age_to", mode="before")
    @classmethod
    def parse_age_values(cls, v) -> Optional[int]:
        """Parse age values that might be strings with ranges or plus signs."""
        if v is None:
            return None

        # If it's already an integer, return it
        if isinstance(v, int):
            return v

        # Convert to string for processing
        value_str = str(v).strip()

        # Handle age ranges like "16+", "16-18", "16 to 18"
        if "+" in value_str:
            # Extract the number before the plus sign
            match = re.match(r"(\d+)\+?", value_str)
            if match:
                return int(match.group(1))

        # Handle ranges like "16-18", "16 to 18", "16-18 years"
        if "-" in value_str or " to " in value_str:
            # Extract the first number in the range
            match = re.match(r"(\d+)", value_str)
            if match:
                return int(match.group(1))

        # Handle plain numbers
        try:
            return int(value_str)
        except (ValueError, TypeError):
            return None


class BookRecommendationSchema(BaseBookRecommendationCriteria):
    """
    Schema for the get_book_recommendation tool.

    Extends BaseBookRecommendationCriteria for tool input validation.
    Maintains backward compatibility with existing tool usage.
    """

    pass


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
