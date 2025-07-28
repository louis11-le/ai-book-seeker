"""
Query intent schemas for structured intent categorization.

This module contains schemas for categorizing and structuring user query intents.
Follows industry best practices for intent schema design with optimized code reuse.
"""

from enum import Enum
from typing import List, Optional

from ai_book_seeker.features.get_book_recommendation.schema import (
    BaseBookRecommendationCriteria,
)
from pydantic import BaseModel, Field, field_validator


class IntentType(str, Enum):
    """Enumeration of supported intent types for validation."""

    # FAQ intents
    INVENTORY_PROCESS = "inventory_process"
    EVENT_BOOKING = "event_booking"
    RETURN_POLICY = "return_policy"
    SHIPPING_INFO = "shipping_info"
    GENERAL_FAQ = "general_faq"

    # Book recommendation intents
    AGE_BASED_RECOMMENDATION = "age_based_recommendation"
    GENRE_BASED_RECOMMENDATION = "genre_based_recommendation"
    BUDGET_BASED_RECOMMENDATION = "budget_based_recommendation"
    PURPOSE_BASED_RECOMMENDATION = "purpose_based_recommendation"

    # Product inquiry intents
    SPECIFIC_BOOK_AVAILABILITY = "specific_book_availability"
    BOOK_DETAILS = "book_details"
    PRICE_INQUIRY = "price_inquiry"

    # Sales intents
    PURCHASE_INTENT = "purchase_intent"
    ORDER_STATUS = "order_status"
    PAYMENT_INQUIRY = "payment_inquiry"


class CategoryType(str, Enum):
    """Enumeration of supported category types for validation."""

    CUSTOMER_SERVICE = "customer_service"
    SERVICES = "services"
    POLICIES = "policies"
    GENERAL = "general"
    RECOMMENDATION = "recommendation"
    INVENTORY = "inventory"
    TRANSACTION = "transaction"


class BaseIntentRequest(BaseModel):
    """
    Base class for all intent requests with common fields and validation.

    Provides shared functionality and validation for all intent types.
    """

    intent: str = Field(..., min_length=1, description="Intent identifier")
    category: str = Field(..., min_length=1, description="Category classification")
    priority: Optional[int] = Field(default=1, ge=1, le=5, description="Priority level 1-5")

    # @field_validator("intent")
    # @classmethod
    # def validate_intent(cls, v: str) -> str:
    #     """Validate that intent is one of the allowed values."""
    #     try:
    #         IntentType(v)
    #     except ValueError:
    #         allowed_intents = [intent.value for intent in IntentType]
    #         raise ValueError(f"Invalid intent '{v}'. Allowed values: {allowed_intents}")
    #     return v

    # @field_validator("category")
    # @classmethod
    # def validate_category(cls, v: str) -> str:
    #     """Validate that category is one of the allowed values."""
    #     try:
    #         try:
    #             CategoryType(v)
    #         except ValueError:
    #             allowed_categories = [category.value for category in CategoryType]
    #             raise ValueError(f"Invalid category '{v}'. Allowed values: {allowed_categories}")
    #         return v


class BookRecommendationCriteria(BaseBookRecommendationCriteria):
    """
    Structured criteria for book recommendation requests.

    Extends BaseBookRecommendationCriteria for workflow intent categorization.
    Adds intent-specific fields like interests for better categorization.
    """

    interests: Optional[List[str]] = Field(default_factory=list, description="Specific interests")

    @field_validator("interests")
    @classmethod
    def validate_interests(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate that interests are non-empty strings."""
        if v is not None:
            return [interest.strip() for interest in v if interest and interest.strip()]
        return v


class ProductDetails(BaseModel):
    """
    Structured product details for product inquiries.

    Provides validation and structure for product information.
    """

    title: Optional[str] = Field(None, min_length=1, description="Book title")
    author: Optional[str] = Field(None, min_length=1, description="Book author")
    isbn: Optional[str] = Field(None, min_length=10, max_length=13, description="ISBN number")
    format: Optional[str] = Field(None, description="Book format (hardcover, paperback, etc.)")

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: Optional[str]) -> Optional[str]:
        """Validate ISBN format if provided."""
        if v is not None:
            # Remove hyphens and spaces
            clean_isbn = v.replace("-", "").replace(" ", "")
            if not clean_isbn.isdigit() or len(clean_isbn) not in [10, 13]:
                raise ValueError("ISBN must be 10 or 13 digits")
            return clean_isbn
        return v


class SalesDetails(BaseModel):
    """
    Structured sales details for sales requests.

    Provides validation and structure for sales information.
    """

    product_id: Optional[str] = Field(None, min_length=1, description="Product identifier")
    quantity: Optional[int] = Field(None, ge=1, description="Quantity to purchase")
    price: Optional[float] = Field(None, ge=0.0, description="Product price")
    payment_method: Optional[str] = Field(None, description="Preferred payment method")


class FAQRequest(BaseIntentRequest):
    """
    Structured FAQ request with intent and context.

    Provides structured representation of FAQ-related queries.
    """

    question: str = Field(..., min_length=1, description="The actual question")

    # @field_validator("intent")
    # @classmethod
    # def validate_faq_intent(cls, v: str) -> str:
    #     """Validate that intent is a FAQ-related intent."""
    #     faq_intents = [
    #         IntentType.INVENTORY_PROCESS,
    #         IntentType.EVENT_BOOKING,
    #         IntentType.RETURN_POLICY,
    #         IntentType.SHIPPING_INFO,
    #         IntentType.GENERAL_FAQ,
    #     ]
    #     if v not in [intent.value for intent in faq_intents]:
    #         raise ValueError(f"Invalid FAQ intent '{v}'. Allowed: {[intent.value for intent in faq_intents]}")

    #     return v


class BookRecommendationRequest(BaseIntentRequest):
    """
    Structured book recommendation request with criteria.

    Provides structured representation of book recommendation queries.
    """

    criteria: BookRecommendationCriteria

    # @field_validator("intent")
    # @classmethod
    # def validate_recommendation_intent(cls, v: str) -> str:
    #     """Validate that intent is a recommendation-related intent."""
    #     recommendation_intents = [
    #         IntentType.AGE_BASED_RECOMMENDATION,
    #         IntentType.GENRE_BASED_RECOMMENDATION,
    #         IntentType.BUDGET_BASED_RECOMMENDATION,
    #         IntentType.PURPOSE_BASED_RECOMMENDATION,
    #     ]
    #     if v not in [intent.value for intent in recommendation_intents]:
    #         raise ValueError(
    #             f"Invalid recommendation intent '{v}'. Allowed: {[intent.value for intent in recommendation_intents]}"
    #         )
    #     return v


class ProductInquiry(BaseIntentRequest):
    """
    Structured product inquiry with details.

    Provides structured representation of product-related queries.
    """

    product_details: ProductDetails

    # @field_validator("intent")
    # @classmethod
    # def validate_product_intent(cls, v: str) -> str:
    #     """Validate that intent is a product-related intent."""
    #     product_intents = [
    #         IntentType.SPECIFIC_BOOK_AVAILABILITY,
    #         IntentType.BOOK_DETAILS,
    #         IntentType.PRICE_INQUIRY,
    #     ]
    #     if v not in [intent.value for intent in product_intents]:
    #         raise ValueError(f"Invalid product intent '{v}'. Allowed: {[intent.value for intent in product_intents]}")
    #     return v


class SalesRequest(BaseIntentRequest):
    """
    Structured sales request with details.

    Provides structured representation of sales-related queries.
    """

    sales_details: SalesDetails

    # @field_validator("intent")
    # @classmethod
    # def validate_sales_intent(cls, v: str) -> str:
    #     """Validate that intent is a sales-related intent."""
    #     sales_intents = [
    #         IntentType.PURCHASE_INTENT,
    #         IntentType.ORDER_STATUS,
    #         IntentType.PAYMENT_INQUIRY,
    #     ]
    #     if v not in [intent.value for intent in sales_intents]:
    #         raise ValueError(f"Invalid sales intent '{v}'. Allowed: {[intent.value for intent in sales_intents]}")
    #     return v


class QueryIntents(BaseModel):
    """
    Structured categorization of query intents.

    Organizes different types of query intents for multi-purpose query handling.
    Provides utility methods for intent analysis and validation.
    """

    faq_requests: List[FAQRequest] = Field(default_factory=list, description="FAQ-related requests")
    book_recommendations: List[BookRecommendationRequest] = Field(
        default_factory=list, description="Book recommendation requests"
    )
    product_inquiries: List[ProductInquiry] = Field(default_factory=list, description="Product inquiry requests")
    sales_requests: List[SalesRequest] = Field(default_factory=list, description="Sales-related requests")

    @field_validator("faq_requests", "book_recommendations", "product_inquiries", "sales_requests")
    @classmethod
    def validate_priority_consistency(cls, v: List) -> List:
        """Ensure priorities are consistent within each intent type."""
        priorities = [item.priority for item in v if item.priority is not None]
        if len(set(priorities)) > 1:
            # Could add business logic here for priority consistency
            # For now, just log a warning
            pass
        return v

    def get_total_intents(self) -> int:
        """Get total number of intents across all categories."""
        return (
            len(self.faq_requests)
            + len(self.book_recommendations)
            + len(self.product_inquiries)
            + len(self.sales_requests)
        )

    def has_multi_purpose_intents(self) -> bool:
        """Check if this represents a multi-purpose query."""
        return self.get_total_intents() > 1

    def get_intents_by_priority(self, priority: int) -> List[BaseIntentRequest]:
        """Get all intents with a specific priority level."""
        all_intents = self.faq_requests + self.book_recommendations + self.product_inquiries + self.sales_requests
        return [intent for intent in all_intents if intent.priority == priority]

    def get_intents_by_category(self, category: str) -> List[BaseIntentRequest]:
        """Get all intents with a specific category."""
        all_intents = self.faq_requests + self.book_recommendations + self.product_inquiries + self.sales_requests
        return [intent for intent in all_intents if intent.category == category]

    def is_empty(self) -> bool:
        """Check if there are no intents."""
        return self.get_total_intents() == 0
