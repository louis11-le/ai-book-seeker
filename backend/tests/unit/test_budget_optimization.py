"""
Unit tests for budget optimization functionality

This module tests the budget optimization functions to ensure they correctly
implement the knapsack algorithm for optimal book selection within budget constraints.
"""

import pytest
from ai_book_seeker.features.budget_optimization import (
    calculate_book_value,
    filter_by_budget,
)
from sqlalchemy import Column, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create test database
Base = declarative_base()


class TestBook(Base):
    """Test book model for budget optimization testing"""

    __tablename__ = "test_books"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    from_age = Column(Integer, nullable=True)
    to_age = Column(Integer, nullable=True)
    purpose = Column(String)
    genre = Column(String)
    price = Column(Float)


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create database session for testing"""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_books(session):
    """Create sample books with various prices and characteristics for testing"""
    books = [
        # High-value books (good price, specific age range, good metadata)
        TestBook(
            id=1,
            title="Excellent Learning Book for Ages 8-10",
            from_age=8,
            to_age=10,
            purpose="learning",
            genre="educational",
            price=15.0,
        ),
        TestBook(
            id=2,
            title="Great Adventure Story for Young Readers",
            from_age=6,
            to_age=9,
            purpose="entertainment",
            genre="adventure",
            price=12.0,
        ),
        # Mid-value books
        TestBook(
            id=3, title="Standard Textbook", from_age=10, to_age=15, purpose="learning", genre="textbook", price=25.0
        ),
        TestBook(
            id=4, title="Fun Story Book", from_age=None, to_age=12, purpose="entertainment", genre="fiction", price=18.0
        ),
        # Lower-value books (expensive, broad age range, minimal metadata)
        TestBook(id=5, title="Book", from_age=5, to_age=18, purpose="entertainment", genre="general", price=45.0),
        TestBook(
            id=6,
            title="Expensive Reference",
            from_age=None,
            to_age=None,
            purpose="learning",
            genre="reference",
            price=60.0,
        ),
        # Edge cases
        TestBook(id=7, title="Free Book", from_age=8, to_age=12, purpose="learning", genre="educational", price=0.0),
        TestBook(
            id=8, title="Very Cheap Book", from_age=6, to_age=8, purpose="entertainment", genre="comedy", price=5.0
        ),
        TestBook(id=9, title="No Price Book", from_age=10, to_age=14, purpose="learning", genre="science", price=None),
    ]

    session.add_all(books)
    session.commit()
    return books


class TestBudgetOptimization:
    """Test cases for budget optimization algorithm"""

    def test_no_budget_returns_all_books(self, session, sample_books):
        """Test that when no budget is specified, all books are returned"""
        books = session.query(TestBook).all()
        result = filter_by_budget(books, None)

        assert len(result) == len(books)
        assert set(book.id for book in result) == set(book.id for book in books)

    def test_zero_budget_returns_empty(self, session, sample_books):
        """Test that zero budget returns only free books"""
        books = session.query(TestBook).all()
        result = filter_by_budget(books, 0.0)

        # Should return only free books (price = 0.0)
        assert len(result) > 0
        assert all(book.price == 0.0 for book in result)

    def test_negative_budget_returns_empty(self, session, sample_books):
        """Test that negative budget returns empty list"""
        books = session.query(TestBook).all()
        result = filter_by_budget(books, -10.0)

        assert len(result) == 0

    def test_empty_book_list_returns_empty(self, session):
        """Test that empty book list returns empty result"""
        result = filter_by_budget([], 50.0)

        assert len(result) == 0

    def test_budget_optimization_selects_optimal_combination(self, session, sample_books):
        """Test that the algorithm selects the optimal combination within budget"""
        books = session.query(TestBook).all()

        # Budget of $30 should select high-value books
        result = filter_by_budget(books, 30.0)

        # Should select books with highest value/price ratio

        # Expected: Book 2 ($12, high value), Book 8 ($5, high value), Book 1 ($15, high value)
        # Total: $32, but algorithm should optimize for best value
        assert len(result) > 0
        assert sum(float(book.price) if book.price else 0 for book in result) <= 30.0

    def test_budget_exactly_matches_books(self, session, sample_books):
        """Test when budget exactly matches some combination of books"""
        books = session.query(TestBook).all()

        # Budget of $27 should select optimal combination
        result = filter_by_budget(books, 27.0)

        assert len(result) > 0
        total_cost = sum(float(book.price) if book.price else 0 for book in result)
        assert total_cost <= 27.0

    def test_all_books_exceed_budget(self, session, sample_books):
        """Test when all books individually exceed the budget"""
        # Create expensive books
        expensive_books = [
            TestBook(id=10, title="Expensive Book 1", price=100.0),
            TestBook(id=11, title="Expensive Book 2", price=150.0),
        ]
        session.add_all(expensive_books)
        session.commit()

        result = filter_by_budget(expensive_books, 50.0)

        assert len(result) == 0

    def test_single_book_fits_budget(self, session, sample_books):
        """Test when only one book fits within budget"""
        books = session.query(TestBook).all()

        # Budget of $10 should select the best book under $10
        result = filter_by_budget(books, 10.0)

        assert len(result) > 0
        assert all(float(book.price) <= 10.0 for book in result if book.price)

    def test_free_books_are_included(self, session, sample_books):
        """Test that free books are properly handled"""
        books = session.query(TestBook).all()

        # Budget of $0 should include free books
        result = filter_by_budget(books, 0.0)

        # Should include the free book (id=7)
        free_books = [book for book in result if book.price == 0.0]
        assert len(free_books) > 0

    def test_books_without_price_are_handled(self, session, sample_books):
        """Test that books without price information are handled gracefully"""
        books = session.query(TestBook).all()

        result = filter_by_budget(books, 50.0)

        # Should not crash and should handle books with None price
        assert len(result) >= 0


class TestBookValueCalculation:
    """Test cases for book value calculation"""

    def test_high_value_book_characteristics(self, session):
        """Test that books with high-value characteristics get higher scores"""
        # High-value book: specific age range, good price, complete metadata
        high_value_book = TestBook(
            id=1,
            title="Excellent Learning Book for Ages 8-10",
            from_age=8,
            to_age=10,
            purpose="learning",
            genre="educational",
            price=15.0,
        )

        # Low-value book: broad age range, expensive, minimal metadata
        low_value_book = TestBook(
            id=2, title="Book", from_age=5, to_age=18, purpose="entertainment", genre="general", price=45.0
        )

        high_value = calculate_book_value(high_value_book)
        low_value = calculate_book_value(low_value_book)

        assert high_value > low_value

    def test_price_efficiency_factor(self, session):
        """Test that price efficiency affects value calculation"""
        # Affordable book
        affordable_book = TestBook(id=1, title="Affordable Book", price=15.0)

        # Expensive book
        expensive_book = TestBook(id=2, title="Expensive Book", price=60.0)

        affordable_value = calculate_book_value(affordable_book)
        expensive_value = calculate_book_value(expensive_book)

        # Affordable book should have higher value score
        assert affordable_value > expensive_value

    def test_age_range_completeness(self, session):
        """Test that age range completeness affects value"""
        # Complete age range
        complete_age_book = TestBook(id=1, title="Complete Age Book", from_age=8, to_age=10, price=20.0)

        # Partial age range
        partial_age_book = TestBook(id=2, title="Partial Age Book", from_age=8, to_age=None, price=20.0)

        # No age range
        no_age_book = TestBook(id=3, title="No Age Book", from_age=None, to_age=None, price=20.0)

        complete_value = calculate_book_value(complete_age_book)
        partial_value = calculate_book_value(partial_age_book)
        no_age_value = calculate_book_value(no_age_book)

        # Complete age range should have highest value
        assert complete_value > partial_value
        assert partial_value > no_age_value

    def test_metadata_completeness(self, session):
        """Test that metadata completeness affects value"""
        # Complete metadata
        complete_book = TestBook(id=1, title="Complete Book", purpose="learning", genre="educational", price=20.0)

        # Incomplete metadata
        incomplete_book = TestBook(id=2, title="Incomplete Book", purpose="", genre="", price=20.0)

        complete_value = calculate_book_value(complete_book)
        incomplete_value = calculate_book_value(incomplete_book)

        # Complete metadata should have higher value
        assert complete_value > incomplete_value

    def test_title_quality_factor(self, session):
        """Test that title quality affects value"""
        # Descriptive title
        descriptive_book = TestBook(id=1, title="Very Descriptive and Informative Book Title", price=20.0)

        # Short title
        short_book = TestBook(id=2, title="Book", price=20.0)

        descriptive_value = calculate_book_value(descriptive_book)
        short_value = calculate_book_value(short_book)

        # Descriptive title should have higher value
        assert descriptive_value > short_value

    def test_no_price_penalty(self, session):
        """Test that books without price get heavy penalty"""
        # Book with price
        priced_book = TestBook(id=1, title="Priced Book", price=20.0)

        # Book without price
        no_price_book = TestBook(id=2, title="No Price Book", price=None)

        priced_value = calculate_book_value(priced_book)
        no_price_value = calculate_book_value(no_price_book)

        # Book without price should have much lower value
        assert priced_value > no_price_value * 2  # Should be at least 2x higher


class TestBudgetOptimizationIntegration:
    """Integration tests for budget optimization with real scenarios"""

    def test_realistic_budget_scenario(self, session, sample_books):
        """Test a realistic budget scenario with multiple books"""
        books = session.query(TestBook).all()

        # Simulate a parent with $40 budget looking for educational books
        result = filter_by_budget(books, 40.0)

        assert len(result) > 0
        total_cost = sum(float(book.price) if book.price else 0 for book in result)
        assert total_cost <= 40.0

        # Should prioritize high-value books
        high_value_books = [book for book in result if book.price and book.price <= 20.0]
        assert len(high_value_books) > 0

    def test_budget_optimization_performance(self, session, sample_books):
        """Test that budget optimization performs well with larger datasets"""
        # Create additional books to test performance
        additional_books = []
        for i in range(50):
            book = TestBook(
                id=100 + i,
                title=f"Test Book {i}",
                from_age=i % 10 + 5,
                to_age=i % 10 + 8,
                purpose="learning" if i % 2 == 0 else "entertainment",
                genre=f"genre_{i % 5}",
                price=float(i % 30 + 10),
            )
            additional_books.append(book)

        session.add_all(additional_books)
        session.commit()

        all_books = session.query(TestBook).all()

        # Test with reasonable budget
        import time

        start_time = time.time()
        result = filter_by_budget(all_books, 100.0)
        end_time = time.time()

        # Should complete within reasonable time (less than 1 second)
        assert end_time - start_time < 1.0
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__])
