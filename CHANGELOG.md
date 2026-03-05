# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - Unreleased

Initial release as a proper Python package.

### Added

- Installable package via `pip install lansweeper-helpdesk`.
- Full type annotations on all public methods and parameters.
- Custom exception hierarchy: `HelpdeskError`, `APIError`, `ConfigurationError`, `TicketNotFoundError`.
- `TicketState` and `NoteType` enums for common API values.
- `py.typed` marker for PEP 561 type checker support.
- Comprehensive test suite using pytest and responses.
- CI pipeline (GitHub Actions) with testing across Python 3.10–3.13, ruff linting, and mypy type checking.
- PyPI publishing workflow via GitHub Releases using trusted publishers (OIDC).

### Changed

- **BREAKING**: Renamed `type` parameter to `note_type` in `add_note()` and `ticket_type` in `edit_ticket()` to avoid shadowing the Python builtin.
- **BREAKING**: Renamed `search_ticket()` to `search_tickets()` with snake_case parameters (`from_user_id`, `agent_id`, `ticket_type`, `max_results`, `min_date`, `max_date`). All parameters are now keyword-only.
- **BREAKING**: API errors now raise `APIError` instead of returning `None`.
- **BREAKING**: `get_ticket_history()` now returns a `list[dict]` of parsed notes instead of a formatted JSON string.
- Replaced all `print()` calls with `logging` — the SDK no longer writes to stdout.
- `cert_path` is now optional (defaults to standard certificate verification).
- Internal request method renamed from `make_request` to `_request`.

### Removed

- `pretty_print_response()` — libraries should not print to stdout; use `json.dumps(response, indent=2)` if needed.
- `usage_decorator` — replaced by proper type annotations and exception handling.
- Hard-coded `time.sleep(1)` in `get_ticket_history()`.
