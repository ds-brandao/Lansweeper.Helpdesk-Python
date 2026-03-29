# lansweeper-helpdesk

[![CI](https://github.com/ds-brandao/Lansweeper.Helpdesk-Python/actions/workflows/ci.yml/badge.svg)](https://github.com/ds-brandao/Lansweeper.Helpdesk-Python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/lansweeper-helpdesk?v=1)](https://pypi.org/project/lansweeper-helpdesk/)
[![Python](https://img.shields.io/pypi/pyversions/lansweeper-helpdesk?v=1)](https://pypi.org/project/lansweeper-helpdesk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python SDK for the [Lansweeper Helpdesk API](https://www.lansweeper.com/). Create, retrieve, search, and manage helpdesk tickets programmatically.

> **Note:** The Lansweeper Helpdesk API appears to be unmaintained and may be deprecated in the future. This SDK wraps the existing API as-is.

## Installation

```bash
pip install lansweeper-helpdesk
```

## Quick Start

```python
from lansweeper_helpdesk import HelpdeskAPI

api = HelpdeskAPI(
    base_url="https://your-helpdesk-url:443/api.aspx",
    api_key="your-api-key",
    cert_path="/path/to/cert.pem",  # optional
)

# Create a ticket
ticket = api.create_ticket(
    subject="Network Issue",
    description="Cannot reach internal network",
    email="user@example.com",
)

# Get ticket details (HTML is auto-stripped)
ticket = api.get_ticket("12345")
print(ticket["Description"])
```

## API Reference

### `HelpdeskAPI(base_url, api_key, cert_path=None)`

Initialize the client.

| Parameter   | Type            | Description                                        |
|-------------|-----------------|----------------------------------------------------|
| `base_url`  | `str`           | Base URL of the Lansweeper Helpdesk API             |
| `api_key`   | `str`           | API key for authentication                          |
| `cert_path` | `str` or `None` | Path to SSL certificate file (optional)             |

### Ticket Operations

#### `create_ticket(subject, description, email) -> dict`

Create a new helpdesk ticket.

```python
api.create_ticket(
    subject="Printer not working",
    description="Office printer on floor 3 is offline",
    email="user@company.com",
)
```

#### `get_ticket(ticket_id) -> dict`

Retrieve ticket details. HTML in the `Description` field is automatically converted to plain text.

```python
ticket = api.get_ticket("12345")
```

#### `get_ticket_history(ticket_id) -> list[dict]`

Get all notes for a ticket. HTML content in note text fields is auto-stripped.

```python
notes = api.get_ticket_history("12345")
for note in notes:
    print(note["Text"])
```

#### `edit_ticket(ticket_id, state, ticket_type, email) -> dict`

Update a ticket's state and type.

```python
api.edit_ticket(
    ticket_id="12345",
    state="Closed",
    ticket_type="Hardware Repair",
    email="agent@company.com",
)
```

### Notes

#### `add_note(ticket_id, text, email, note_type="Public") -> dict`

Add a note to a ticket. Use `note_type="Internal"` for agent-only notes.

```python
api.add_note(
    ticket_id="12345",
    text="Router restart resolved the issue",
    email="agent@company.com",
    note_type="Internal",
)
```

### Search

#### `search_tickets(*, state, from_user_id, agent_id, description, subject, ticket_type, max_results, min_date, max_date) -> dict`

Search tickets with optional filters. All parameters are keyword-only and optional.

```python
results = api.search_tickets(
    state="Open",
    ticket_type="Hardware Repair",
    max_results=50,
    min_date="2024-01-01",
    max_date="2024-12-31",
)
```

#### `get_user(email) -> dict`

Look up a user by email address.

```python
user = api.get_user("user@company.com")
```

### Enums

The SDK provides convenience enums for common values:

```python
from lansweeper_helpdesk import TicketState, NoteType

api.search_tickets(state=TicketState.OPEN)
api.add_note("12345", "note text", "a@b.com", note_type=NoteType.INTERNAL)
```

### Error Handling

All API methods raise typed exceptions instead of returning `None`:

```python
from lansweeper_helpdesk import HelpdeskAPI, APIError, ConfigurationError

try:
    api = HelpdeskAPI(base_url="", api_key="key")
except ConfigurationError as e:
    print(f"Bad config: {e}")

try:
    ticket = api.get_ticket("99999")
except APIError as e:
    print(f"API error (HTTP {e.status_code}): {e}")
```

| Exception              | When                                              |
|------------------------|----------------------------------------------------|
| `HelpdeskError`        | Base class for all SDK exceptions                  |
| `ConfigurationError`   | Invalid client configuration                       |
| `APIError`             | HTTP or API-level error (has `.status_code`)       |
| `TicketNotFoundError`  | Requested ticket does not exist                    |

## Configuration

You can load credentials from a JSON config file:

```python
import json
from lansweeper_helpdesk import HelpdeskAPI

with open("config/config.json") as f:
    config = json.load(f)

api = HelpdeskAPI(**config)
```

Example `config/config.json`:

```json
{
    "base_url": "https://your-helpdesk-url:443/api.aspx",
    "api_key": "your-api-key-here",
    "cert_path": "path/to/your/certificate.pem"
}
```

## Development

```bash
# Clone and install in dev mode
git clone https://github.com/ds-brandao/Lansweeper.Helpdesk-Python.git
cd Lansweeper.Helpdesk-Python
pip install -e ".[dev]"

# Run tests
pytest --cov

# Lint & format
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.
