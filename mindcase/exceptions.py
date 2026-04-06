"""Mindcase SDK exceptions."""

from typing import Optional


class MindcaseError(Exception):
    """Base exception for all Mindcase SDK errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        super().__init__(message)


class AuthenticationError(MindcaseError):
    """Invalid or missing API key (401)."""
    pass


class InsufficientCreditsError(MindcaseError):
    """Not enough credits to run the agent (402)."""
    pass


class NotFoundError(MindcaseError):
    """Agent, job, or resource not found (404)."""
    pass


class RateLimitError(MindcaseError):
    """Rate limit exceeded (429). Retry after 60 seconds."""
    pass


class ValidationError(MindcaseError):
    """Invalid parameters (422)."""
    pass
