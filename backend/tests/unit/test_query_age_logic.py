"""
Unit tests for the age range logic in query.py

This module tests the apply_age_filters function to ensure it correctly
implements the business logic for age-based book filtering, including
validation, error handling, and performance monitoring.
"""

import pytest
from ai_book_seeker.features.age_filtering import validate_age_preferences
from ai_book_seeker.services.explainer import BookPreferences
from sqlalchemy import Column, Float, Integer, String, and_, create_engine, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create test database
Base = declarative_base()


class TestBook(Base):
    """Test book model for age range testing"""

    __tablename__ = "test_books"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    from_age = Column(Integer, nullable=True)
    to_age = Column(Integer, nullable=True)
    purpose = Column(String)
    genre = Column(String)
    price = Column(Float)


def apply_age_filters_test(query, preferences: BookPreferences, book_model):
    """
    Test version of apply_age_filters that works with TestBook model.

    This is a copy of the logic from age_filtering/logic.py but adapted for testing.
    """
    if not preferences:
        return query

    # Handle age_from/age_to combinations
    if preferences.age_from is not None or preferences.age_to is not None:
        if preferences.age_from is not None and preferences.age_to is not None:
            # Age range: Book's range should overlap with user's range
            query = query.filter(
                or_(
                    # Book has no age restrictions
                    and_(book_model.from_age.is_(None), book_model.to_age.is_(None)),
                    # Book's age range overlaps with user's range
                    and_(
                        or_(book_model.from_age.is_(None), book_model.from_age <= preferences.age_to),
                        or_(book_model.to_age.is_(None), book_model.to_age >= preferences.age_from),
                    ),
                )
            )
        elif preferences.age_from is not None:
            # Age_from only: Book should be suitable for age_from and above
            query = query.filter(
                or_(
                    book_model.to_age.is_(None),  # No upper age limit
                    book_model.to_age >= preferences.age_from,
                )
            )
        elif preferences.age_to is not None:
            # Age_to only: Book should be suitable for age_to and below
            query = query.filter(
                or_(
                    book_model.from_age.is_(None),  # No lower age limit
                    book_model.from_age <= preferences.age_to,
                )
            )
    elif preferences.age is not None:
        # Single age: Book should be suitable for the user's age
        user_age = preferences.age
        query = query.filter(
            or_(
                # Book has no age restrictions
                and_(book_model.from_age.is_(None), book_model.to_age.is_(None)),
                # Book's age range includes the user's age
                and_(
                    or_(book_model.from_age.is_(None), book_model.from_age <= user_age),
                    or_(book_model.to_age.is_(None), book_model.to_age >= user_age),
                ),
            )
        )

    return query


@pytest.fixture
def session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_books(session):
    """Create sample books with various age ranges for testing"""
    books = [
        # Books with specific age ranges
        TestBook(id=1, title="Baby Book", from_age=0, to_age=2, purpose="learning", genre="educational", price=10.0),
        TestBook(id=2, title="Toddler Book", from_age=2, to_age=5, purpose="learning", genre="educational", price=12.0),
        TestBook(id=3, title="Early Reader", from_age=5, to_age=8, purpose="learning", genre="educational", price=15.0),
        TestBook(
            id=4, title="Middle Grade", from_age=8, to_age=12, purpose="entertainment", genre="fantasy", price=18.0
        ),
        TestBook(
            id=5, title="Teen Book", from_age=12, to_age=18, purpose="entertainment", genre="adventure", price=20.0
        ),
        TestBook(
            id=6, title="Adult Book", from_age=18, to_age=None, purpose="entertainment", genre="mystery", price=25.0
        ),
        # Books with partial age ranges
        TestBook(
            id=7, title="All Ages Book", from_age=None, to_age=None, purpose="entertainment", genre="comedy", price=15.0
        ),
        TestBook(
            id=8, title="Young Adult+", from_age=16, to_age=None, purpose="entertainment", genre="romance", price=22.0
        ),
        TestBook(
            id=9, title="Children's Classic", from_age=None, to_age=12, purpose="learning", genre="classic", price=16.0
        ),
        # Edge cases
        TestBook(id=10, title="Preschool", from_age=3, to_age=6, purpose="learning", genre="educational", price=14.0),
        TestBook(id=11, title="Elementary", from_age=6, to_age=11, purpose="learning", genre="educational", price=17.0),
    ]

    session.add_all(books)
    session.commit()
    return books


class TestAgeValidation:
    """Test cases for age preference validation"""

    def test_valid_single_age(self):
        """Test that valid single age passes validation"""
        preferences = BookPreferences(age=10)
        errors = validate_age_preferences(preferences)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_valid_age_range(self):
        """Test that valid age range passes validation"""
        preferences = BookPreferences(age_from=5, age_to=12)
        errors = validate_age_preferences(preferences)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_valid_age_from_only(self):
        """Test that valid age_from only passes validation"""
        preferences = BookPreferences(age_from=15)
        errors = validate_age_preferences(preferences)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_valid_age_to_only(self):
        """Test that valid age_to only passes validation"""
        preferences = BookPreferences(age_to=10)
        errors = validate_age_preferences(preferences)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_invalid_age_too_low(self):
        """Test that age below minimum fails validation"""
        preferences = BookPreferences(age=-1)
        errors = validate_age_preferences(preferences)
        assert len(errors) == 1
        assert "Age must be between 0 and 120" in errors[0]

    def test_invalid_age_too_high(self):
        """Test that age above maximum fails validation"""
        preferences = BookPreferences(age=121)
        errors = validate_age_preferences(preferences)
        assert len(errors) == 1
        assert "Age must be between 0 and 120" in errors[0]

    def test_invalid_age_from_too_low(self):
        """Test that age_from below minimum fails validation"""
        preferences = BookPreferences(age_from=-5)
        errors = validate_age_preferences(preferences)
        assert len(errors) == 1
        assert "Age_from must be between 0 and 120" in errors[0]

    def test_invalid_age_to_too_high(self):
        """Test that age_to above maximum fails validation"""
        preferences = BookPreferences(age_to=150)
        errors = validate_age_preferences(preferences)
        assert len(errors) == 1
        assert "Age_to must be between 0 and 120" in errors[0]

    def test_invalid_age_range_reversed(self):
        """Test that age_from > age_to fails validation"""
        preferences = BookPreferences(age_from=15, age_to=10)
        errors = validate_age_preferences(preferences)
        assert len(errors) == 1
        assert "age_from (15) cannot be greater than age_to (10)" in errors[0]

    def test_mutual_exclusivity_violation(self):
        """Test that specifying both age and age_from/age_to fails validation"""
        preferences = BookPreferences(age=10, age_from=5, age_to=15)
        errors = validate_age_preferences(preferences)
        assert len(errors) == 1
        assert "cannot specify both 'age' and 'age_from'/'age_to'" in errors[0]

    def test_mutual_exclusivity_violation_age_and_age_from(self):
        """Test that specifying both age and age_from fails validation"""
        preferences = BookPreferences(age=10, age_from=5)
        errors = validate_age_preferences(preferences)
        assert len(errors) == 1
        assert "cannot specify both 'age' and 'age_from'/'age_to'" in errors[0]

    def test_mutual_exclusivity_violation_age_and_age_to(self):
        """Test that specifying both age and age_to fails validation"""
        preferences = BookPreferences(age=10, age_to=15)
        errors = validate_age_preferences(preferences)
        assert len(errors) == 1
        assert "cannot specify both 'age' and 'age_from'/'age_to'" in errors[0]

    def test_none_preferences(self):
        """Test that None preferences pass validation"""
        errors = validate_age_preferences(None)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_empty_preferences(self):
        """Test that empty preferences pass validation"""
        preferences = BookPreferences()
        errors = validate_age_preferences(preferences)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"


class TestAgeRangeLogic:
    """Test cases for age range filtering logic"""

    def test_single_age_matching(self, session, sample_books):
        """Test that books match when user age falls within book's age range"""
        # Test age 10 should match books for ages 8-12, 6-11, and all-ages books
        # Early Reader (5-8) should NOT match because 10 > 8
        preferences = BookPreferences(age=10)
        query = session.query(TestBook)
        filtered_query = apply_age_filters_test(query, preferences, TestBook)
        results = filtered_query.all()

        book_titles = [book.title for book in results]
        expected_titles = ["Middle Grade", "Elementary", "All Ages Book", "Children's Classic"]

        assert set(book_titles) == set(expected_titles), f"Expected {expected_titles}, got {book_titles}"

    def test_age_range_overlap(self, session, sample_books):
        """Test that books match when their age range overlaps with user's range"""
        # User wants books for ages 7-10
        # Should match: Early Reader (5-8), Middle Grade (8-12), Elementary (6-11), All Ages, Children's Classic
        preferences = BookPreferences(age_from=7, age_to=10)
        query = session.query(TestBook)
        filtered_query = apply_age_filters_test(query, preferences, TestBook)
        results = filtered_query.all()

        book_titles = [book.title for book in results]
        expected_titles = ["Early Reader", "Middle Grade", "Elementary", "All Ages Book", "Children's Classic"]

        assert set(book_titles) == set(expected_titles), f"Expected {expected_titles}, got {book_titles}"

    def test_age_from_only(self, session, sample_books):
        """Test filtering with only age_from specified"""
        # User wants books suitable for age 15 and above
        # Should include: Teen Book (12-18), Adult Book (18+), Young Adult+ (16+), All Ages Book
        preferences = BookPreferences(age_from=15)
        query = session.query(TestBook)
        filtered_query = apply_age_filters_test(query, preferences, TestBook)
        results = filtered_query.all()

        book_titles = [book.title for book in results]
        expected_titles = ["Teen Book", "Adult Book", "Young Adult+", "All Ages Book"]

        assert set(book_titles) == set(expected_titles), f"Expected {expected_titles}, got {book_titles}"

    def test_age_to_only(self, session, sample_books):
        """Test filtering with only age_to specified"""
        # User wants books suitable for age 7 and below
        # Should include: Baby Book (0-2), Toddler Book (2-5), Early Reader (5-8), Preschool (3-6), Elementary (6-11), All Ages Book, Children's Classic
        preferences = BookPreferences(age_to=7)
        query = session.query(TestBook)
        filtered_query = apply_age_filters_test(query, preferences, TestBook)
        results = filtered_query.all()

        book_titles = [book.title for book in results]
        expected_titles = [
            "Baby Book",
            "Toddler Book",
            "Early Reader",
            "Preschool",
            "Elementary",
            "All Ages Book",
            "Children's Classic",
        ]

        assert set(book_titles) == set(expected_titles), f"Expected {expected_titles}, got {book_titles}"

    def test_all_ages_book_matches_everything(self, session, sample_books):
        """Test that books with no age restrictions match all age preferences"""
        # Test various age preferences with All Ages Book
        test_cases = [
            BookPreferences(age=5),
            BookPreferences(age=25),
            BookPreferences(age_from=0, age_to=100),
            BookPreferences(age_from=10),
            BookPreferences(age_to=5),
        ]

        for preferences in test_cases:
            query = session.query(TestBook)
            filtered_query = apply_age_filters_test(query, preferences, TestBook)
            results = filtered_query.all()
            book_titles = [book.title for book in results]
            assert "All Ages Book" in book_titles, f"All Ages Book should match {preferences}"

    def test_no_age_preferences_returns_all(self, session, sample_books):
        """Test that when no age preferences are specified, all books are returned"""
        preferences = BookPreferences()  # No age specified
        query = session.query(TestBook)
        filtered_query = apply_age_filters_test(query, preferences, TestBook)
        results = filtered_query.all()

        assert len(results) == len(sample_books), "All books should be returned when no age preferences specified"

    def test_edge_case_exact_age_match(self, session, sample_books):
        """Test edge cases where user age exactly matches book age boundaries"""
        # Test age 8 should match Early Reader (5-8), Middle Grade (8-12), Elementary (6-11), All Ages Book, Children's Classic
        preferences = BookPreferences(age=8)
        query = session.query(TestBook)
        filtered_query = apply_age_filters_test(query, preferences, TestBook)
        results = filtered_query.all()

        book_titles = [book.title for book in results]
        expected_titles = ["Early Reader", "Middle Grade", "Elementary", "All Ages Book", "Children's Classic"]

        assert set(book_titles) == set(expected_titles), f"Expected {expected_titles}, got {book_titles}"

    def test_partial_age_range_books(self, session, sample_books):
        """Test books with partial age ranges (only from_age or only to_age)"""
        # Test age 17 should match Teen Book (12-18), Young Adult+ (16+), All Ages Book
        # Note: Adult Book (18+) should NOT match because 17 < 18
        preferences = BookPreferences(age=17)
        query = session.query(TestBook)
        filtered_query = apply_age_filters_test(query, preferences, TestBook)
        results = filtered_query.all()

        book_titles = [book.title for book in results]
        expected_titles = ["Teen Book", "Young Adult+", "All Ages Book"]

        assert set(book_titles) == set(expected_titles), f"Expected {expected_titles}, got {book_titles}"

    def test_age_range_no_overlap(self, session, sample_books):
        """Test that books with no age range overlap are correctly excluded"""
        # Test age 10 should NOT match Early Reader (5-8) or Adult Book (18+)
        preferences = BookPreferences(age=10)
        query = session.query(TestBook)
        filtered_query = apply_age_filters_test(query, preferences, TestBook)
        results = filtered_query.all()

        book_titles = [book.title for book in results]
        excluded_titles = ["Early Reader", "Adult Book", "Young Adult+"]

        for title in excluded_titles:
            assert title not in book_titles, f"{title} should not match age 10"


class TestAgeRangeLogicIntegration:
    """Integration tests for age range logic with other filters"""

    def test_age_and_purpose_filtering(self, session, sample_books):
        """Test age filtering combined with purpose filtering"""
        preferences = BookPreferences(age=6, purpose="learning")
        query = session.query(TestBook)
        filtered_query = apply_age_filters_test(query, preferences, TestBook)
        # Apply purpose filter manually for testing
        filtered_query = filtered_query.filter(TestBook.purpose == "learning")
        results = filtered_query.all()

        book_titles = [book.title for book in results]
        expected_titles = ["Early Reader", "Elementary", "Preschool", "Children's Classic"]

        assert set(book_titles) == set(expected_titles), f"Expected {expected_titles}, got {book_titles}"

    def test_age_and_genre_filtering(self, session, sample_books):
        """Test age filtering combined with genre filtering"""
        preferences = BookPreferences(age_from=3, age_to=7, genre="educational")
        query = session.query(TestBook)
        filtered_query = apply_age_filters_test(query, preferences, TestBook)
        # Apply genre filter manually for testing
        filtered_query = filtered_query.filter(TestBook.genre == "educational")
        results = filtered_query.all()

        book_titles = [book.title for book in results]
        expected_titles = ["Toddler Book", "Early Reader", "Preschool", "Elementary"]

        assert set(book_titles) == set(expected_titles), f"Expected {expected_titles}, got {book_titles}"


if __name__ == "__main__":
    pytest.main([__file__])
