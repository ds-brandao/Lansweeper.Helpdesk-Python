"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from lansweeper_helpdesk import HelpdeskAPI


@pytest.fixture()
def cert_file(tmp_path: Path) -> str:
    """Create a temporary dummy certificate file and return its path."""
    cert = tmp_path / "cert.pem"
    cert.write_text("dummy-cert-content")
    return str(cert)


@pytest.fixture()
def api(cert_file: str) -> HelpdeskAPI:
    """Create a HelpdeskAPI instance configured for testing."""
    return HelpdeskAPI(
        base_url="https://helpdesk.example.com/api.aspx",
        api_key="test-api-key",
        cert_path=cert_file,
    )


@pytest.fixture()
def api_no_cert() -> HelpdeskAPI:
    """Create a HelpdeskAPI instance without a custom certificate."""
    return HelpdeskAPI(
        base_url="https://helpdesk.example.com/api.aspx",
        api_key="test-api-key",
    )
