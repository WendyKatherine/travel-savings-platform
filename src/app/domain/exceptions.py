"""
exceptions.py — Domain exception hierarchy.

The API layer maps ONLY these exceptions to HTTP error responses.
Keeping a dedicated base class (instead of raising bare ValueError)
means a programming bug that happens to raise ValueError still
surfaces as a 500, while intentional domain rejections map to a
clean 4xx.
"""


class DomainError(Exception):
    """Base class for every intentional domain rejection."""
