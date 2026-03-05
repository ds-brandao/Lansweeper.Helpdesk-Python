"""Tests for type definitions."""

from __future__ import annotations

from lansweeper_helpdesk.types import NoteType, TicketState


class TestTicketState:
    def test_values(self) -> None:
        assert TicketState.OPEN == "Open"
        assert TicketState.CLOSED == "Closed"

    def test_is_string(self) -> None:
        assert isinstance(TicketState.OPEN, str)


class TestNoteType:
    def test_values(self) -> None:
        assert NoteType.PUBLIC == "Public"
        assert NoteType.INTERNAL == "Internal"

    def test_is_string(self) -> None:
        assert isinstance(NoteType.PUBLIC, str)
