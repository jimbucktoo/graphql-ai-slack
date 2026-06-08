"""Slash command handlers for the GraphQLAI Slack app."""

import logging
import threading
from typing import Callable

from slack_bolt import App

from services.graphqlai_client import GraphQLAIClient, GraphQLAIClientError
from utils.block_kit import (
    format_error_response,
    format_success_response,
    format_usage_response,
    format_validation_error_response,
)

logger = logging.getLogger(__name__)

SLASH_COMMAND = "/graphql"


def register_slash_commands(app: App, client: GraphQLAIClient) -> None:
    """Attach all slash command handlers to the Bolt app."""

    @app.command(SLASH_COMMAND)
    def handle_graphql_command(ack: Callable, body: dict, respond: Callable) -> None:
        """Handle the /graphql slash command."""
        ack()

        prompt: str = body.get("text", "").strip()
        if not prompt:
            respond(blocks=format_usage_response(), text="GraphQLAI usage")
            return

        def process() -> None:
            logger.info("Received /graphql command: prompt=%r", prompt)
            try:
                response = client.generate_query(prompt)
            except GraphQLAIClientError as exc:
                logger.error("GraphQLAI client error: %s", exc)
                respond(blocks=format_error_response(str(exc)), text="GraphQLAI error")
                return

            if client.is_success(response):
                query = client.extract_query(response)
                respond(
                    blocks=format_success_response(query, prompt),
                    text=f"GraphQL query generated for: {prompt}",
                )
            else:
                attempted = client.extract_query(response)
                errors = response.get("validation_errors", [])
                logger.warning("Validation errors for prompt=%r errors=%s", prompt, errors)
                respond(
                    blocks=format_validation_error_response(attempted, errors, prompt),
                    text="GraphQLAI could not generate a valid query",
                )

        threading.Thread(target=process).start()
