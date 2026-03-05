"""Lansweeper Helpdesk API client."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import requests
from bs4 import BeautifulSoup

from lansweeper_helpdesk.exceptions import APIError, ConfigurationError
from lansweeper_helpdesk.types import APIResponse

logger = logging.getLogger(__name__)


class HelpdeskAPI:
    """Client for the Lansweeper Helpdesk API.

    Provides methods to create, retrieve, search, and manage helpdesk tickets,
    add notes, and look up users.

    Args:
        base_url: The base URL of the Lansweeper Helpdesk API
            (e.g. ``"https://helpdesk.example.com:443/api.aspx"``).
        api_key: API key for authentication.
        cert_path: Optional path to an SSL certificate file for verification.
            When ``None``, standard certificate verification is used.

    Raises:
        ConfigurationError: If ``base_url`` or ``api_key`` is not provided.
        FileNotFoundError: If ``cert_path`` is given but the file does not exist.

    Example::

        from lansweeper_helpdesk import HelpdeskAPI

        api = HelpdeskAPI(
            base_url="https://helpdesk.example.com:443/api.aspx",
            api_key="your-api-key",
            cert_path="/path/to/cert.pem",
        )
        ticket = api.get_ticket("12345")
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        cert_path: str | None = None,
    ) -> None:
        if not base_url:
            raise ConfigurationError("base_url must be provided.")
        if not api_key:
            raise ConfigurationError("api_key must be provided.")

        self.base_url = base_url
        self.api_key = api_key

        self.session = requests.Session()

        if cert_path is not None:
            if not os.path.isfile(cert_path):
                raise FileNotFoundError(f"Certificate file not found: {cert_path}")
            self.session.verify = cert_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(
        self,
        action: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> APIResponse | str:
        """Make an HTTP request to the Lansweeper Helpdesk API.

        Args:
            action: The API action to perform (e.g. ``"AddTicket"``).
            method: HTTP method — ``"GET"`` or ``"POST"``.
            params: Extra query/form parameters.
            files: Files to upload with the request.

        Returns:
            Parsed JSON response as a dict, or raw text if the response is not JSON.

        Raises:
            APIError: If the request fails or the server returns an error status.
        """
        request_params: dict[str, Any] = {
            "Action": action,
            "Key": self.api_key,
            **(params or {}),
        }

        logger.debug("Making %s request for action=%s", method, action)

        try:
            if method == "POST":
                response = self.session.post(self.base_url, data=request_params, files=files)
            else:
                response = self.session.get(self.base_url, params=request_params)

            response.raise_for_status()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            body = exc.response.text if exc.response is not None else None
            raise APIError(f"HTTP {status} for action {action}", status_code=status, response_body=body) from exc
        except requests.RequestException as exc:
            raise APIError(f"Request failed for action {action}: {exc}") from exc

        logger.debug("Response status: %s", response.status_code)

        if not response.text:
            raise APIError(f"Empty response for action {action}", status_code=response.status_code)

        try:
            return response.json()  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            return response.text

    @staticmethod
    def _strip_html(html: str) -> str:
        """Convert an HTML string to plain text."""
        return BeautifulSoup(html, "html.parser").get_text()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_ticket(self, subject: str, description: str, email: str) -> APIResponse:
        """Create a new helpdesk ticket.

        Args:
            subject: The subject line of the ticket.
            description: Detailed description of the issue.
            email: Email address of the ticket requester.

        Returns:
            API response containing the created ticket data.

        Raises:
            APIError: If ticket creation fails.

        Example::

            api.create_ticket(
                subject="Network Issue",
                description="Cannot reach internal network",
                email="user@example.com",
            )
        """
        params = {
            "Subject": subject,
            "Description": description,
            "Email": email,
        }
        response = self._request("AddTicket", method="POST", params=params)
        if isinstance(response, str):
            raise APIError(f"Unexpected non-JSON response: {response}")
        return response

    def get_ticket(self, ticket_id: str) -> APIResponse:
        """Retrieve details of a specific ticket.

        HTML in the ``Description`` field is automatically converted to plain text.

        Args:
            ticket_id: The unique identifier of the ticket.

        Returns:
            Ticket information dict.

        Raises:
            APIError: If the request fails.

        Example::

            ticket = api.get_ticket("12345")
            print(ticket["Description"])
        """
        response = self._request("GetTicket", params={"TicketID": ticket_id})
        if isinstance(response, str):
            raise APIError(f"Unexpected non-JSON response: {response}")

        if "Description" in response:
            response["Description"] = self._strip_html(response["Description"])
        return response

    def get_ticket_history(self, ticket_id: str) -> list[APIResponse]:
        """Retrieve the complete history of a ticket including all notes.

        HTML content inside individual note fields is converted to plain text.

        Args:
            ticket_id: The unique identifier of the ticket.

        Returns:
            List of note dicts for the ticket.

        Raises:
            APIError: If the request fails.
        """
        response = self._request("GetNotes", params={"TicketID": ticket_id})
        if isinstance(response, str):
            raise APIError(f"Unexpected non-JSON response: {response}")

        notes: list[APIResponse] = response.get("Notes") or []

        # Strip HTML from text fields inside each note
        for note in notes:
            for key in ("Text", "Description"):
                if key in note and isinstance(note[key], str):
                    note[key] = self._strip_html(note[key])

        return notes

    def add_note(
        self,
        ticket_id: str,
        text: str,
        email: str,
        note_type: str = "Public",
    ) -> APIResponse:
        """Add a note to an existing ticket.

        Args:
            ticket_id: The unique identifier of the ticket.
            text: The note content.
            email: Email address of the note author.
            note_type: ``"Public"`` (visible to requester) or ``"Internal"``.

        Returns:
            API response confirming note addition.

        Raises:
            APIError: If the request fails.

        Example::

            api.add_note(
                ticket_id="12345",
                text="Investigated — router restart required",
                email="agent@example.com",
                note_type="Internal",
            )
        """
        params = {
            "TicketID": ticket_id,
            "Text": text,
            "Email": email,
            "Type": note_type,
        }
        response = self._request("AddNote", method="POST", params=params)
        if isinstance(response, str):
            raise APIError(f"Unexpected non-JSON response: {response}")
        return response

    def search_tickets(
        self,
        *,
        state: str | None = None,
        from_user_id: str | None = None,
        agent_id: str | None = None,
        description: str | None = None,
        subject: str | None = None,
        ticket_type: str | None = None,
        max_results: int | None = None,
        min_date: str | None = None,
        max_date: str | None = None,
    ) -> APIResponse:
        """Search for tickets matching the given criteria.

        All parameters are optional filters. Only non-``None`` values are sent
        to the API.

        Args:
            state: Ticket state (e.g. ``"Open"``, ``"Closed"``).
            from_user_id: ID of the ticket creator.
            agent_id: ID of the assigned agent.
            description: Text to search in ticket descriptions.
            subject: Text to search in ticket subjects.
            ticket_type: Ticket type (e.g. ``"Hardware Repair"``).
            max_results: Maximum number of results to return.
            min_date: Start date filter (``YYYY-MM-DD``).
            max_date: End date filter (``YYYY-MM-DD``).

        Returns:
            API response containing matching tickets.

        Raises:
            APIError: If the request fails.

        Example::

            results = api.search_tickets(
                state="Open",
                ticket_type="Hardware Repair",
                max_results=50,
            )
        """
        param_map: dict[str, Any] = {
            "State": state,
            "FromUserId": from_user_id,
            "AgentId": agent_id,
            "Description": description,
            "Subject": subject,
            "Type": ticket_type,
            "MaxResults": max_results,
            "MinDate": min_date,
            "MaxDate": max_date,
        }
        params = {k: v for k, v in param_map.items() if v is not None}
        response = self._request("SearchTickets", params=params)
        if isinstance(response, str):
            raise APIError(f"Unexpected non-JSON response: {response}")
        return response

    def get_user(self, email: str) -> APIResponse:
        """Look up a user by email address.

        Args:
            email: Email address of the user.

        Returns:
            User information dict.

        Raises:
            APIError: If the request fails.

        Example::

            user = api.get_user("user@example.com")
        """
        response = self._request("SearchUsers", params={"Email": email})
        if isinstance(response, str):
            raise APIError(f"Unexpected non-JSON response: {response}")
        return response

    def edit_ticket(
        self,
        ticket_id: str,
        state: str,
        ticket_type: str,
        email: str,
    ) -> APIResponse:
        """Update an existing ticket's properties.

        Args:
            ticket_id: The unique identifier of the ticket.
            state: New state (e.g. ``"Open"``, ``"Closed"``).
            ticket_type: New ticket type (e.g. ``"Hardware Repair"``).
            email: Email of the person making the edit.

        Returns:
            API response confirming the update.

        Raises:
            APIError: If the request fails.

        Example::

            api.edit_ticket(
                ticket_id="12345",
                state="Closed",
                ticket_type="Hardware Repair",
                email="agent@example.com",
            )
        """
        params = {
            "TicketID": ticket_id,
            "State": state,
            "Type": ticket_type,
            "Email": email,
        }
        response = self._request("EditTicket", method="POST", params=params)
        if isinstance(response, str):
            raise APIError(f"Unexpected non-JSON response: {response}")
        return response
