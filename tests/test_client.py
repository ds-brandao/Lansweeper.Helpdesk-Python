"""Tests for the HelpdeskAPI client."""

from __future__ import annotations

import pytest
import responses

from lansweeper_helpdesk import HelpdeskAPI
from lansweeper_helpdesk.exceptions import APIError, ConfigurationError

BASE_URL = "https://helpdesk.example.com/api.aspx"


# ------------------------------------------------------------------
# Constructor tests
# ------------------------------------------------------------------


class TestInit:
    def test_missing_base_url(self) -> None:
        with pytest.raises(ConfigurationError, match="base_url"):
            HelpdeskAPI(base_url="", api_key="key")

    def test_missing_api_key(self) -> None:
        with pytest.raises(ConfigurationError, match="api_key"):
            HelpdeskAPI(base_url="https://example.com", api_key="")

    def test_bad_cert_path(self) -> None:
        with pytest.raises(FileNotFoundError, match="does-not-exist"):
            HelpdeskAPI(base_url="https://example.com", api_key="key", cert_path="/does-not-exist.pem")

    def test_no_cert_uses_default_verification(self, api_no_cert: HelpdeskAPI) -> None:
        # session.verify should remain True (requests default)
        assert api_no_cert.session.verify is True

    def test_cert_path_set(self, api: HelpdeskAPI, cert_file: str) -> None:
        assert api.session.verify == cert_file


# ------------------------------------------------------------------
# create_ticket
# ------------------------------------------------------------------


class TestCreateTicket:
    @responses.activate
    def test_success(self, api: HelpdeskAPI) -> None:
        responses.add(
            responses.POST,
            BASE_URL,
            json={"TicketID": "100", "Result": "Success"},
            status=200,
        )
        result = api.create_ticket(subject="Test", description="A test ticket", email="u@example.com")
        assert result["TicketID"] == "100"

    @responses.activate
    def test_server_error(self, api: HelpdeskAPI) -> None:
        responses.add(responses.POST, BASE_URL, body="Internal Server Error", status=500)
        with pytest.raises(APIError, match="500"):
            api.create_ticket(subject="Test", description="Desc", email="u@example.com")


# ------------------------------------------------------------------
# get_ticket
# ------------------------------------------------------------------


class TestGetTicket:
    @responses.activate
    def test_success_strips_html(self, api: HelpdeskAPI) -> None:
        responses.add(
            responses.GET,
            BASE_URL,
            json={"TicketID": "100", "Description": "<p>Hello <b>world</b></p>"},
            status=200,
        )
        result = api.get_ticket("100")
        assert result["Description"] == "Hello world"

    @responses.activate
    def test_no_description_key(self, api: HelpdeskAPI) -> None:
        responses.add(
            responses.GET,
            BASE_URL,
            json={"TicketID": "100", "Subject": "Test"},
            status=200,
        )
        result = api.get_ticket("100")
        assert "Description" not in result


# ------------------------------------------------------------------
# get_ticket_history
# ------------------------------------------------------------------


class TestGetTicketHistory:
    @responses.activate
    def test_returns_notes_with_html_stripped(self, api: HelpdeskAPI) -> None:
        responses.add(
            responses.GET,
            BASE_URL,
            json={
                "Notes": [
                    {"Text": "<p>Note one</p>", "Author": "agent"},
                    {"Text": "<b>Note two</b>", "Author": "user"},
                ]
            },
            status=200,
        )
        notes = api.get_ticket_history("100")
        assert len(notes) == 2
        assert notes[0]["Text"] == "Note one"
        assert notes[1]["Text"] == "Note two"

    @responses.activate
    def test_empty_notes(self, api: HelpdeskAPI) -> None:
        responses.add(responses.GET, BASE_URL, json={"Notes": []}, status=200)
        notes = api.get_ticket_history("100")
        assert notes == []

    @responses.activate
    def test_null_notes(self, api: HelpdeskAPI) -> None:
        responses.add(responses.GET, BASE_URL, json={"Notes": None}, status=200)
        notes = api.get_ticket_history("100")
        assert notes == []


# ------------------------------------------------------------------
# add_note
# ------------------------------------------------------------------


class TestAddNote:
    @responses.activate
    def test_success(self, api: HelpdeskAPI) -> None:
        responses.add(responses.POST, BASE_URL, json={"Result": "Success"}, status=200)
        result = api.add_note(ticket_id="100", text="A note", email="a@b.com", note_type="Internal")
        assert result["Result"] == "Success"

    @responses.activate
    def test_default_note_type(self, api: HelpdeskAPI) -> None:
        responses.add(responses.POST, BASE_URL, json={"Result": "Success"}, status=200)
        api.add_note(ticket_id="100", text="A note", email="a@b.com")
        assert responses.calls[0].request.body is not None
        assert "Type=Public" in responses.calls[0].request.body


# ------------------------------------------------------------------
# search_tickets
# ------------------------------------------------------------------


class TestSearchTickets:
    @responses.activate
    def test_with_filters(self, api: HelpdeskAPI) -> None:
        responses.add(
            responses.GET,
            BASE_URL,
            json={"Tickets": [{"TicketID": "1"}, {"TicketID": "2"}]},
            status=200,
        )
        result = api.search_tickets(state="Open", max_results=10)
        assert "Tickets" in result
        # Verify query params
        request_url = responses.calls[0].request.url or ""
        assert "State=Open" in request_url
        assert "MaxResults=10" in request_url

    @responses.activate
    def test_no_filters(self, api: HelpdeskAPI) -> None:
        responses.add(responses.GET, BASE_URL, json={"Tickets": []}, status=200)
        result = api.search_tickets()
        assert result == {"Tickets": []}


# ------------------------------------------------------------------
# get_user
# ------------------------------------------------------------------


class TestGetUser:
    @responses.activate
    def test_success(self, api: HelpdeskAPI) -> None:
        responses.add(
            responses.GET,
            BASE_URL,
            json={"UserID": "42", "Email": "u@example.com"},
            status=200,
        )
        result = api.get_user("u@example.com")
        assert result["UserID"] == "42"


# ------------------------------------------------------------------
# edit_ticket
# ------------------------------------------------------------------


class TestEditTicket:
    @responses.activate
    def test_success(self, api: HelpdeskAPI) -> None:
        responses.add(responses.POST, BASE_URL, json={"Result": "Success"}, status=200)
        result = api.edit_ticket(ticket_id="100", state="Closed", ticket_type="Network", email="a@b.com")
        assert result["Result"] == "Success"


# ------------------------------------------------------------------
# _request edge cases
# ------------------------------------------------------------------


class TestRequest:
    @responses.activate
    def test_empty_response_raises(self, api: HelpdeskAPI) -> None:
        responses.add(responses.GET, BASE_URL, body="", status=200)
        with pytest.raises(APIError, match="Empty response"):
            api.get_ticket("100")

    @responses.activate
    def test_non_json_response(self, api: HelpdeskAPI) -> None:
        responses.add(responses.GET, BASE_URL, body="plain text response", status=200)
        # get_ticket expects JSON — non-JSON raises APIError
        with pytest.raises(APIError, match="non-JSON"):
            api.get_ticket("100")

    @responses.activate
    def test_http_error_includes_status(self, api: HelpdeskAPI) -> None:
        responses.add(responses.GET, BASE_URL, body="Not Found", status=404)
        with pytest.raises(APIError) as exc_info:
            api.get_ticket("999")
        assert exc_info.value.status_code == 404
