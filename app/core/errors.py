"""
Domain errors and exceptions.
This module contains custom exceptions specific to the domain.
"""

from typing import Any, Dict, Optional


class DomainError(Exception):
    """Base class for domain-specific errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(DomainError):
    """Raised when domain validation fails."""

    pass


class NotFoundError(DomainError):
    """Raised when a requested resource is not found."""

    pass


class BusinessRuleViolation(DomainError):
    """Raised when a business rule is violated."""

    pass
