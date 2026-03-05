"""Lansweeper Helpdesk API SDK.

A Python client for creating, retrieving, searching, and managing
tickets in the Lansweeper Helpdesk system.
"""

from lansweeper_helpdesk.client import HelpdeskAPI
from lansweeper_helpdesk.exceptions import (
    APIError,
    ConfigurationError,
    HelpdeskError,
    TicketNotFoundError,
)
from lansweeper_helpdesk.types import NoteType, TicketState

__version__ = "0.1.0"

__all__ = [
    "HelpdeskAPI",
    "APIError",
    "ConfigurationError",
    "HelpdeskError",
    "TicketNotFoundError",
    "NoteType",
    "TicketState",
    "__version__",
]
