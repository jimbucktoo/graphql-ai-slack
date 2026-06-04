"""GraphQLAI Slack — entry point. Wiring only; no business logic here."""

import logging
import os

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from handlers.slash_commands import register_slash_commands
from handlers.workflows import register_workflow_steps
from services.graphqlai_client import DEFAULT_API_URL, GraphQLAIClient

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

APP_NAME = "GraphQLAI Slack"

REQUIRED_ENV_VARS = [
    "SLACK_BOT_TOKEN",
    "SLACK_SIGNING_SECRET",
    "SLACK_APP_TOKEN",
    "GRAPHQL_ENDPOINT",
]


def _validate_env() -> None:
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        raise EnvironmentError(
            f"{APP_NAME} cannot start. Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and populate the values."
        )


def create_app() -> tuple[App, str]:
    _validate_env()

    api_url = os.getenv("GRAPHQLAI_API_URL", DEFAULT_API_URL)
    graphql_endpoint = os.getenv("GRAPHQL_ENDPOINT", "")

    graphqlai_client = GraphQLAIClient(api_url=api_url, graphql_endpoint=graphql_endpoint)

    bolt_app = App(
        token=os.getenv("SLACK_BOT_TOKEN"),
        signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
    )

    register_slash_commands(bolt_app, graphqlai_client)
    register_workflow_steps(bolt_app, graphqlai_client)

    return bolt_app, os.getenv("SLACK_APP_TOKEN", "")


if __name__ == "__main__":
    app, app_token = create_app()
    logger.info(
        "%s started | commands=[/graphql] | workflow_steps=[generate_graphql_query] | api=%s",
        APP_NAME,
        os.getenv("GRAPHQLAI_API_URL", DEFAULT_API_URL),
    )
    SocketModeHandler(app, app_token).start()
