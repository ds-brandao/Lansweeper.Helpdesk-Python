"""Type definitions for the Lansweeper Helpdesk SDK."""

from __future__ import annotations

import sys
from enum import Enum
from typing import Any

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:

    class StrEnum(str, Enum):
        """String enum backport for Python 3.10."""


class TicketState(StrEnum):
    """Possible states for a helpdesk ticket."""

    OPEN = "Open"
    CLOSED = "Closed"


class NoteType(StrEnum):
    """Types of notes that can be added to a ticket."""

    PUBLIC = "Public"
    INTERNAL = "Internal"


# Type alias for API responses
APIResponse = dict[str, Any]
