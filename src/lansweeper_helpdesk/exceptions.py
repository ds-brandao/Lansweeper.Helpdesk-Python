"""Custom exceptions for the Lansweeper Helpdesk SDK."""

from __future__ import annotations


class HelpdeskError(Exception):
    """Base exception for all lansweeper-helpdesk errors."""


class ConfigurationError(HelpdeskError):
    """Raised for invalid client configuration (missing URL, bad cert path, etc.)."""


class APIError(HelpdeskError):
    """Raised when the API returns an error response.

    Attributes:
        status_code: HTTP status code from the response, if available.
        response_body: Raw response body text, if available.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class TicketNotFoundError(APIError):
    """Raised when a requested ticket does not exist."""
