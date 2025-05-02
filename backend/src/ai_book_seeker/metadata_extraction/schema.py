"""
Schema definitions for metadata extraction.

This module defines Pydantic models for structured metadata output in the metadata extraction feature.
"""

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class PublicationDetails(BaseModel):
    """Publication details model."""

    publisher: Optional[str] = Field(None, description="Publisher name")
    publication_date: Optional[str] = Field(None, description="Publication date")
    edition: Optional[str] = Field(None, description="Edition information")
    isbn: Optional[str] = Field(None, description="ISBN number")
    pages: Optional[Union[int, str]] = Field(None, description="Number of pages")

    @field_validator("pages")
    @classmethod
    def validate_pages(cls, v: Optional[Union[int, str]]) -> Optional[int]:
        """Convert string pages to integer or None."""
        if not v or isinstance(v, str) and v.lower() in ["not specified", "unknown", ""]:
            return None

        return int(v) if isinstance(v, str) else v


class TargetAudience(BaseModel):
    """Target audience model."""

    age_range: Optional[str] = Field(None, description="Target age range")
    from_age: Optional[int] = Field(None, description="Lower bound of target age range")
    to_age: Optional[int] = Field(None, description="Upper bound of target age range")
    grade_level: Optional[str] = Field(None, description="Target grade level")
    special_interests: Optional[List[str]] = Field(None, description="Special interest categories")


class NormalizedMetadata(BaseModel):
    """Normalized metadata model."""

    title: str = Field(description="Book title")
    author: str = Field(description="Author name")
    description: str = Field(description="Book description")
    age_range: str = Field(description="Target age range")
    purpose: str = Field(description="Book purpose (max 3 words)")
    genre: str = Field(description="Book genre (max 3 words)")
    tags: List[str] = Field(description="List of tags")
    publication_details: PublicationDetails = Field(description="Publication details")
    language: str = Field(description="Book language")
    target_audience: TargetAudience = Field(description="Target audience information")


class ValidationStatus(BaseModel):
    """Validation status model."""

    is_valid: bool = Field(description="Whether the metadata is valid")
    missing_fields: List[str] = Field(default_factory=list, description="List of missing required fields")
    valid_fields: List[str] = Field(default_factory=list, description="List of valid fields")


class ErrorReports(BaseModel):
    """Error reports model."""

    errors: Dict[str, str] = Field(default_factory=dict, description="Error messages by field")
    warnings: Dict[str, str] = Field(default_factory=dict, description="Warning messages by field")


class ConfidenceScores(BaseModel):
    """Confidence scores model."""

    overall: float = Field(description="Overall confidence score (0-1)")
    fields: Dict[str, float] = Field(default_factory=dict, description="Confidence scores by field (0-1)")


class QualityAssessment(BaseModel):
    """Quality assessment model."""

    summary: str = Field(description="Quality assessment summary")


class MetadataOutput(BaseModel):
    """Complete metadata output model."""

    normalized_metadata: NormalizedMetadata = Field(description="Normalized metadata")
    validation_status: ValidationStatus = Field(description="Validation status")
    error_reports: ErrorReports = Field(description="Error reports")
    confidence_scores: ConfidenceScores = Field(description="Confidence scores")
    quality_assessment: QualityAssessment = Field(description="Quality assessment")
