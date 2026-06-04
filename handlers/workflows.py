"""Slack Workflow Builder step handler for GraphQLAI."""

import logging
from typing import Callable

from slack_bolt import App
from slack_bolt.workflows.step import WorkflowStep

from services.graphqlai_client import GraphQLAIClient, GraphQLAIClientError

logger = logging.getLogger(__name__)

STEP_CALLBACK_ID = "generate_graphql_query"


def register_workflow_steps(app: App, client: GraphQLAIClient) -> None:
    """Attach the GraphQLAI Workflow Builder step to the Bolt app."""

    def edit(ack: Callable, step: dict, configure: Callable) -> None:
        """Present a modal for the workflow step configuration."""
        ack()
        configure(
            blocks=[
                {
                    "type": "input",
                    "block_id": "query_block",
                    "label": {"type": "plain_text", "text": "What do you want to query?"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "plain_english_query",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "e.g. get all users with their name and email",
                        },
                        "multiline": False,
                    },
                }
            ]
        )

    def save(ack: Callable, step: dict, update: Callable) -> None:
        """Persist the workflow step inputs."""
        ack()
        values = step.get("inputs", {})
        plain_english_query = (
            values.get("query_block", {})
            .get("plain_english_query", {})
            .get("value", "")
        )
        update(inputs={"plain_english_query": {"value": plain_english_query}})

    def execute(step: dict, complete: Callable, fail: Callable) -> None:
        """Run the workflow step by calling the GraphQLAI API."""
        prompt: str = step.get("inputs", {}).get("plain_english_query", {}).get("value", "")
        logger.info("Workflow step executing: prompt=%r", prompt)
        try:
            response = client.generate_query(prompt)
        except GraphQLAIClientError as exc:
            logger.error("Workflow step failed: %s", exc)
            fail(error={"message": str(exc)})
            return

        query = client.extract_query(response)
        if not query:
            errors = response.get("validation_errors", ["Unknown validation error"])
            fail(error={"message": f"Validation failed: {'; '.join(errors)}"})
            return

        complete(
            outputs={
                "graphql_query": query,
                "original_prompt": prompt,
            }
        )

    ws = WorkflowStep(
        callback_id=STEP_CALLBACK_ID,
        edit=edit,
        save=save,
        execute=execute,
    )
    app.step(ws)
    logger.info("Registered workflow step: %s", STEP_CALLBACK_ID)
