"""Test module for math utility functions."""
from main import add, subtract


def test_add():
    """Test the add function with positive numbers."""
    assert add(3, 2) == 5


def test_subtract():
    """Test the subtract function with positive numbers."""
    assert subtract(5, 3) == 2
