"""Mindcase Python SDK — programmatic access to 34+ data collection agents."""

from mindcase.client import Mindcase
from mindcase.exceptions import (
    MindcaseError,
    AuthenticationError,
    InsufficientCreditsError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from mindcase.types import (
    Agent,
    AgentSummary,
    Job,
    JobResults,
    Parameter,
)

__version__ = "0.4.0"
__all__ = [
    "Mindcase",
    # Exceptions
    "MindcaseError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    # Types
    "Agent",
    "AgentSummary",
    "Job",
    "JobResults",
    "Parameter",
]
