"""
Lansweeper Helpdesk API Wrapper

A Python wrapper for interacting with the Lansweeper Helpdesk API.
Provides methods for ticket management, user lookup, and note handling.

Example:
    >>> from helpdesk import HelpdeskAPI
    >>> api = HelpdeskAPI.from_config('config/config.json')
    >>> with api:
    ...     ticket = api.get_ticket('12345')
"""

from __future__ import annotations

import functools
import json
import logging
import os
import time
from typing import Any, Callable, TypeVar

import requests
from bs4 import BeautifulSoup


# Configure module logger
logger = logging.getLogger(__name__)


# Type variable for generic function wrapper
F = TypeVar('F', bound=Callable[..., Any])


# =============================================================================
# Custom Exceptions
# =============================================================================


class HelpdeskError(Exception):
    """Base exception for Helpdesk API errors."""
    pass


class ConfigurationError(HelpdeskError):
    """Raised when there's a configuration error."""
    pass


class APIError(HelpdeskError):
    """Raised when an API request fails."""

    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class CertificateError(HelpdeskError):
    """Raised when there's an SSL certificate error."""
    pass


# =============================================================================
# Helpdesk API Client
# =============================================================================


class HelpdeskAPI:
    """A wrapper class for the Lansweeper Helpdesk API.

    This class provides methods to interact with the Lansweeper Helpdesk API,
    including creating, retrieving, and managing tickets, adding notes, and
    searching users.

    Attributes:
        base_url: The base URL of the Lansweeper Helpdesk API.
        api_key: The API key for authentication.
        cert_path: Path to the SSL certificate file.

    Example:
        >>> api = HelpdeskAPI(
        ...     base_url='https://helpdesk.example.com/api.aspx',
        ...     api_key='your-api-key',
        ...     cert_path='/path/to/cert.pem'
        ... )
        >>> with api:
        ...     ticket = api.get_ticket('12345')
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        cert_path: str
    ) -> None:
        """Initialize the HelpdeskAPI client.

        Args:
            base_url: The base URL of the Lansweeper Helpdesk API.
            api_key: The API key for authentication.
            cert_path: Path to the SSL certificate file.

        Raises:
            ConfigurationError: If base_url or api_key is not provided.
            CertificateError: If the certificate file is not found.
        """
        if not base_url or not api_key:
            raise ConfigurationError("Base URL and API key must be provided.")

        if not cert_path:
            raise ConfigurationError("Certificate path must be provided.")

        if not os.path.isfile(cert_path):
            raise CertificateError(f"Certificate file not found: {cert_path}")

        self._base_url = base_url
        self._api_key = api_key
        self._cert_path = cert_path
        self._session: requests.Session | None = None

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def base_url(self) -> str:
        """Get the base URL of the API."""
        return self._base_url

    @property
    def cert_path(self) -> str:
        """Get the certificate path."""
        return self._cert_path

    @property
    def session(self) -> requests.Session:
        """Get the requests session, creating one if necessary."""
        if self._session is None:
            self._session = requests.Session()
            self._session.verify = self._cert_path
        return self._session

    # =========================================================================
    # Class Methods
    # =========================================================================

    @classmethod
    def from_config(cls, config_path: str) -> HelpdeskAPI:
        """Create a HelpdeskAPI instance from a configuration file.

        Args:
            config_path: Path to the JSON configuration file.

        Returns:
            A configured HelpdeskAPI instance.

        Raises:
            ConfigurationError: If the config file cannot be read or is invalid.

        Example:
            >>> api = HelpdeskAPI.from_config('config/config.json')
        """
        if not os.path.isfile(config_path):
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except IOError as e:
            raise ConfigurationError(f"Error reading configuration file: {e}")

        required_keys = ['base_url', 'api_key', 'cert_path']
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ConfigurationError(
                f"Missing required configuration keys: {', '.join(missing_keys)}"
            )

        return cls(
            base_url=config['base_url'],
            api_key=config['api_key'],
            cert_path=config['cert_path']
        )

    # =========================================================================
    # Context Manager Support
    # =========================================================================

    def __enter__(self) -> HelpdeskAPI:
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context manager and close the session."""
        self.close()

    def close(self) -> None:
        """Close the requests session and release resources."""
        if self._session is not None:
            self._session.close()
            self._session = None
            logger.debug("Session closed")

    # =========================================================================
    # String Representations
    # =========================================================================

    def __repr__(self) -> str:
        """Return a detailed string representation of the object."""
        return (
            f"{self.__class__.__name__}("
            f"base_url={self._base_url!r}, "
            f"cert_path={self._cert_path!r})"
        )

    def __str__(self) -> str:
        """Return a user-friendly string representation of the object."""
        return f"HelpdeskAPI connected to {self._base_url}"

    # =========================================================================
    # Static Methods
    # =========================================================================

    @staticmethod
    def _usage_decorator(func: F) -> F:
        """Decorator that catches TypeError and prints usage information.

        Args:
            func: The function to wrap.

        Returns:
            The wrapped function.
        """
        @functools.wraps(func)
        def wrapper(self: HelpdeskAPI, *args: Any, **kwargs: Any) -> Any:
            try:
                return func(self, *args, **kwargs)
            except TypeError as e:
                logger.error(f"Incorrect usage of {func.__name__}: {e}")
                logger.info(f"Usage: {func.__doc__}")
                return None
        return wrapper  # type: ignore

    # =========================================================================
    # Utility Methods
    # =========================================================================

    @staticmethod
    def format_response(response: dict[str, Any] | None) -> str:
        """Format an API response as a pretty-printed JSON string.

        Args:
            response: The API response to format.

        Returns:
            Formatted JSON string or error message.
        """
        if response:
            return json.dumps(response, indent=4, sort_keys=True)
        return "No response or an error occurred."

    def _make_request(
        self,
        action: str,
        method: str = 'GET',
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None
    ) -> dict[str, Any] | str | None:
        """Make an HTTP request to the Lansweeper Helpdesk API.

        Args:
            action: The API action to perform.
            method: HTTP method to use ('GET' or 'POST'). Defaults to 'GET'.
            params: Query parameters to include.
            data: Data to send in the request body.
            files: Files to upload.

        Returns:
            The API response, parsed as JSON if possible, otherwise as raw text.
            None if the request fails or returns an empty response.

        Raises:
            APIError: If the request fails (only when raise_on_error is True).
        """
        params = params or {}
        data = data or {}

        params['Action'] = action
        params['Key'] = self._api_key

        logger.debug(f"Making {method} request to {self._base_url} with action: {action}")

        try:
            if method.upper() == 'GET':
                response = self.session.get(self._base_url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(self._base_url, data=params, files=files)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()
            logger.debug(f"Response Status Code: {response.status_code}")

            if not response.text:
                logger.warning("Empty response received")
                return None

            logger.debug(f"Raw Response Text: {response.text[:200]}...")

            try:
                return response.json()
            except json.JSONDecodeError:
                logger.debug("Response is not in JSON format, returning raw text")
                return response.text

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    @staticmethod
    def _html_to_text(html: str) -> str:
        """Convert HTML content to plain text.

        Args:
            html: HTML content to convert.

        Returns:
            Plain text extracted from HTML.
        """
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()

    # =========================================================================
    # Ticket Operations
    # =========================================================================

    @_usage_decorator
    def create_ticket(
        self,
        subject: str,
        description: str,
        email: str
    ) -> dict[str, Any] | None:
        """Create a new ticket in the helpdesk system.

        Args:
            subject: The subject line of the ticket.
            description: Detailed description of the issue or request.
            email: Email address of the ticket requester.

        Returns:
            The API response containing the created ticket information,
            or None if the ticket creation fails.

        Example:
            >>> api.create_ticket(
            ...     subject="Network Issue",
            ...     description="Unable to connect to internal network",
            ...     email="user@example.com"
            ... )
        """
        params = {
            'Subject': subject,
            'Description': description,
            'Email': email,
        }
        response = self._make_request('AddTicket', method='POST', params=params)
        logger.info(f"Created ticket: {self.format_response(response)}")
        return response

    @_usage_decorator
    def get_ticket(self, ticket_id: str) -> dict[str, Any] | None:
        """Retrieve details of a specific ticket.

        Args:
            ticket_id: The unique identifier of the ticket.

        Returns:
            Ticket information including status, description, and metadata.
            HTML in description field is automatically converted to plain text.
            None if the ticket retrieval fails or ticket doesn't exist.

        Example:
            >>> api.get_ticket("12345")
        """
        params = {'TicketID': ticket_id}
        response = self._make_request('GetTicket', method='GET', params=params)

        if response and isinstance(response, dict):
            if 'Description' in response:
                response['Description'] = self._html_to_text(response['Description'])
            logger.debug(f"Retrieved ticket {ticket_id}")
        else:
            logger.warning(f"No response received for ticket {ticket_id}")

        return response

    @_usage_decorator
    def get_ticket_history(self, ticket_id: str) -> str | None:
        """Retrieve the complete history of a ticket including all notes and updates.

        Args:
            ticket_id: The unique identifier of the ticket.

        Returns:
            Formatted JSON string containing the ticket's history.
            Includes all notes with HTML content converted to plain text.
            None if the history retrieval fails.

        Note:
            This method includes a 1-second delay between requests to
            prevent API rate limiting.
        """
        params = {'TicketID': ticket_id}
        ticket_info = []

        response = self._make_request('GetNotes', method='GET', params=params)

        if not response:
            logger.warning(f"No response received for ticket history {ticket_id}")
            return None

        if isinstance(response, dict) and response.get('Notes') is not None:
            notes = []
            for note in response['Notes']:
                note_str = json.dumps(note)
                soup = BeautifulSoup(note_str, 'html.parser')
                notes.append(soup.get_text())
            response['Notes'] = '\n\n'.join(notes)
            ticket_info.append(response)

        # Pause to prevent rate limiting
        time.sleep(1)

        # Parse and format the ticket history
        for ticket in ticket_info:
            if 'Notes' in ticket:
                notes = ticket['Notes'].split('\n\n')
                parsed_notes = []
                for note in notes:
                    if note.strip():
                        try:
                            parsed_notes.append(json.loads(note))
                        except json.JSONDecodeError:
                            logger.debug(f"Note is not JSON format, keeping as text")
                            parsed_notes.append(note)
                ticket['Notes'] = parsed_notes

        logger.debug(f"Retrieved history for ticket {ticket_id}")
        return json.dumps(ticket_info, indent=4)

    @_usage_decorator
    def add_note(
        self,
        ticket_id: str,
        text: str,
        email: str,
        note_type: str
    ) -> dict[str, Any] | None:
        """Add a note to an existing ticket.

        Args:
            ticket_id: The unique identifier of the ticket.
            text: The content of the note to add.
            email: Email address of the note author.
            note_type: Type of note - either 'Public' or 'Internal'.

        Returns:
            The API response confirming note addition,
            or None if adding the note fails.

        Example:
            >>> api.add_note(
            ...     ticket_id="12345",
            ...     text="Updated status with customer",
            ...     email="agent@example.com",
            ...     note_type="Public"
            ... )
        """
        logger.info(f"Adding note to ticket {ticket_id}")
        logger.debug(f"Note text length: {len(text)}, Email: {email}, Type: {note_type}")

        params = {
            'TicketID': ticket_id,
            'Text': text,
            'Email': email,
            'Type': note_type
        }

        try:
            response = self._make_request('AddNote', method='POST', params=params)
            logger.debug(f"Add note response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error in add_note: {e}", exc_info=True)
            return None

    @_usage_decorator
    def search_tickets(
        self,
        state: str | None = None,
        from_user_id: str | None = None,
        agent_id: str | None = None,
        description: str | None = None,
        subject: str | None = None,
        ticket_type: str | None = None,
        max_results: int | None = None,
        min_date: str | None = None,
        max_date: str | None = None
    ) -> dict[str, Any] | None:
        """Search for tickets based on various criteria.

        Args:
            state: Ticket state ('Open', 'Closed', etc.).
            from_user_id: ID of the ticket creator.
            agent_id: ID of the assigned agent.
            description: Search text in ticket description.
            subject: Search text in ticket subject.
            ticket_type: Ticket type (e.g., 'Hardware Repair', 'Network').
            max_results: Maximum number of results to return.
            min_date: Start date for ticket search (format: YYYY-MM-DD).
            max_date: End date for ticket search (format: YYYY-MM-DD).

        Returns:
            List of matching ticket IDs and their information,
            or None if the search fails.

        Note:
            If max_results is set lower than the actual number of matching
            tickets, the API will return an empty list.

        Example:
            >>> api.search_tickets(
            ...     state="Open",
            ...     ticket_type="Hardware Repair",
            ...     max_results=50
            ... )
        """
        params = {
            'State': state,
            'FromUserId': from_user_id,
            'AgentId': agent_id,
            'Description': description,
            'Subject': subject,
            'Type': ticket_type,
            'MaxResults': max_results,
            'MinDate': min_date,
            'MaxDate': max_date
        }
        # Remove keys with None values
        params = {k: v for k, v in params.items() if v is not None}

        response = self._make_request('SearchTickets', method='GET', params=params)
        logger.debug(f"Search returned: {self.format_response(response)}")
        return response

    @_usage_decorator
    def edit_ticket(
        self,
        ticket_id: str,
        state: str,
        ticket_type: str,
        email: str
    ) -> dict[str, Any] | None:
        """Update an existing ticket's properties.

        Args:
            ticket_id: The unique identifier of the ticket to edit.
            state: New state for the ticket ('Open', 'Closed', etc.).
            ticket_type: New type for the ticket (e.g., 'Hardware Repair').
            email: Email address of the person making the edit.

        Returns:
            The API response confirming ticket updates,
            or None if the ticket update fails.

        Example:
            >>> api.edit_ticket(
            ...     ticket_id="12345",
            ...     state="Closed",
            ...     ticket_type="Hardware Repair",
            ...     email="agent@example.com"
            ... )
        """
        params = {
            'TicketID': ticket_id,
            'State': state,
            'Type': ticket_type,
            'Email': email
        }
        response = self._make_request('EditTicket', method='POST', params=params)
        logger.info(f"Edited ticket {ticket_id}: {self.format_response(response)}")
        return response

    # =========================================================================
    # User Operations
    # =========================================================================

    @_usage_decorator
    def get_user(self, email: str) -> dict[str, Any] | None:
        """Retrieve user information by email address.

        Args:
            email: Email address of the user to look up.

        Returns:
            User information including ID and profile details,
            or None if the user is not found or lookup fails.

        Example:
            >>> api.get_user("user@example.com")
        """
        params = {'Email': email}
        response = self._make_request('SearchUsers', method='GET', params=params)
        logger.debug(f"User lookup for {email}: {self.format_response(response)}")
        return response
