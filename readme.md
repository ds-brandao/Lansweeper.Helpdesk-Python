# Helpdesk API Python Wrapper

I created this wrapper to make it easier to interact with the Lansweeper Helpdesk API and integrate it with other projects that I am working on that require helpdesk integration. This is a work in progress and I will be adding more features as I need them, there are many requests that are available in the original Lansweeper Helpdesk API that are not available in this wrapper.

It seems like the Lansweeper Helpdesk API is a bit of a mess and I have no idea what the future holds for it, looks like it is not being maintained and may be deprecated in the future or it is already deprecated.

If you find this useful, please feel free to contribute to the project and make it better!!!

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Initialization](#initialization)
- [Usage](#usage)
  - [Create Ticket](#create-ticket)
  - [Get Ticket](#get-ticket)
  - [Get Ticket History](#get-ticket-history)
  - [Add Note](#add-note)
  - [Search Tickets](#search-tickets)
  - [Get User](#get-user)
  - [Edit Ticket](#edit-ticket)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Ticket Management**: Create, retrieve, and edit helpdesk tickets.
- **Notes Handling**: Add notes to existing tickets and retrieve full ticket history.
- **Searching**: Search for tickets based on various parameters (state, type, dates, etc.).
- **User Lookup**: Retrieve user information from the helpdesk system by email.

## Requirements

- `requests`
- `bs4`
- A valid base URL, API key, and a corresponding certificate file for SSL verification.

## Installation

1. Clone this repository

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Initialization

To use the API wrapper, you'll need to initialize it with your credentials:

```python
from helpdesk import HelpdeskAPI

api = HelpdeskAPI(
    base_url="https://your-helpdesk-url/api",
    api_key="your-api-key",
    cert_path="path/to/your/certificate.pem"
)
```

## Usage

### Create Ticket

Create a new ticket in the helpdesk system:

```python
response = api.create_ticket(
    subject="Network Connection Issue",
    description="User unable to connect to internal network",
    email="user@company.com" # The API takes in either an email or an username. Email is easier when tagging a svc_account.
)
```

### Get Ticket

Retrieve details of a specific ticket:

```python
ticket = api.get_ticket("12345")
# HTML in description is automatically converted to plain text
print(ticket['Description'])
```

### Get Ticket History

Retrieve the complete history of a ticket including all notes:

```python
history = api.get_ticket_history("12345")
# Returns formatted JSON string with HTML content converted to plain text
```

### Add Note

Add a note to an existing ticket:

```python
response = api.add_note(
    ticket_id="12345",
    text="Investigated the issue - router restart required",
    email="technician@company.com",
    type="Internal"  # or "Public" (Public is visible to the user)
)
```

### Search Tickets

Search for tickets using various filters:

```python
# Search for open hardware repair tickets
tickets = api.search_ticket(
    state="Open",
    Type="Hardware Repair",
    MaxResults=50,
    MinDate="2024-01-01",
    MaxDate="2024-12-31"
)

# Available search parameters:
# - state: Ticket state (Open, Closed, etc.)
# - FromUserId: ID of ticket creator
# - AgentId: ID of assigned agent
# - Description: Search in ticket description
# - Subject: Search in ticket subject
# - Type: Ticket type
# - MaxResults: Maximum number of results (default 100) - If the number of tickets returned is greater than the MaxResults, the API will bitch about it.
# - MinDate: Start date (YYYY-MM-DD)
# - MaxDate: End date (YYYY-MM-DD)
```

### Get User

Look up user information by email:

```python
user_info = api.get_user("user@company.com")
```

### Edit Ticket

Update an existing ticket's properties:

```python
response = api.edit_ticket(
    ticket_id="12345",
    state="Closed",
    type="Hardware Repair",
    email="technician@company.com"
)
```

## Configuration

Use a `config.json` file in the config directory:

```json
{
    "base_url": "https://your-helpdesk-url/api",
    "api_key": "your-api-key",
    "cert_path": "path/to/your/certificate.pem"
}
```

Then load it:

```python
import json

with open('config/config.json') as f:
    config = json.load(f)

api = HelpdeskAPI(**config)
```

## Contributing

Not sure if there are many using the helpdesk but if you are interested in contributing, please do so.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

What is this?

## Notes

- Rate limiting is built into certain methods (e.g., `get_ticket_history`)
- HTML content in descriptions and notes is automatically converted to plain text
- The `MaxResults` parameter in search_ticket must be greater than or equal to the number of matching tickets