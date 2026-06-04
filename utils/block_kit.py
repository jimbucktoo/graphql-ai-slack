"""Slack Block Kit message formatting helpers."""

APP_NAME = "GraphQLAI"
API_HOST = "graphql-ai-api.onrender.com"


def _mrkdwn(text: str) -> dict:
    return {"type": "mrkdwn", "text": text}


def _header(text: str) -> dict:
    return {"type": "header", "text": {"type": "plain_text", "text": text, "emoji": True}}


def _section(text: str) -> dict:
    return {"type": "section", "text": _mrkdwn(text)}


def _divider() -> dict:
    return {"type": "divider"}


def _context(text: str) -> dict:
    return {"type": "context", "elements": [_mrkdwn(text)]}


def format_success_response(query: str, prompt: str) -> list:
    """Return Block Kit blocks for a successful query generation."""
    return [
        _header(f"⚡ {APP_NAME}"),
        _section(f'Query generated for: *"{prompt}"*'),
        _divider(),
        _section(f"```{query}```"),
        _divider(),
        _context(f"{API_HOST} • /graphql {prompt}"),
    ]


def format_validation_error_response(
    attempted_query: str, errors: list, prompt: str
) -> list:
    """Return Block Kit blocks when the API returns validation errors."""
    errors_text = "\n".join(f"• {e}" for e in errors)
    return [
        _header(f"⚠️ {APP_NAME} — Validation Errors"),
        _section(f'Could not generate a valid query for: *"{prompt}"*'),
        _divider(),
        _section(f"*Best attempt:*\n```{attempted_query}```"),
        _section(f"*Errors:*\n{errors_text}"),
        _context("Try rephrasing your request"),
    ]


def format_error_response(error_message: str) -> list:
    """Return Block Kit blocks for a client-level error."""
    return [
        _header(f"❌ {APP_NAME} — Error"),
        _section(error_message),
        _context("Check that the GraphQL endpoint is reachable and try again"),
    ]


def format_usage_response() -> list:
    """Return Block Kit blocks explaining how to use the slash command."""
    return [
        _header(f"⚡ {APP_NAME}"),
        _section("*Usage:* `/graphql <plain English description of what you want>`"),
        _section(
            "*Examples:*\n"
            "• `/graphql get all users with their name and email`\n"
            "• `/graphql find all posts with their title and author`\n"
            "• `/graphql show comments on post with id 1`"
        ),
    ]
