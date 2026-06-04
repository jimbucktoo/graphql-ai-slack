"""HTTP client for the existing GraphQLAI API."""

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
DEFAULT_API_URL = "https://graphql-ai-api.onrender.com"


class GraphQLAIClientError(Exception):
    """Raised when the GraphQLAI API call fails at the network or HTTP level."""


class GraphQLAIClient:
    """Wraps the deployed GraphQLAI API to generate schema-compliant GraphQL queries."""

    def __init__(self, api_url: str, graphql_endpoint: str) -> None:
        self.api_url = api_url.rstrip("/")
        self.graphql_endpoint = graphql_endpoint

    def generate_query(self, prompt: str) -> dict:
        """Call the GraphQLAI API and return the raw response dict.

        Raises:
            GraphQLAIClientError: on network failure or non-2xx HTTP status.
        """
        payload = {"prompt": prompt, "endpoint": self.graphql_endpoint}
        url = f"{self.api_url}/query"
        logger.debug("POST %s payload=%s", url, payload)
        try:
            response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise GraphQLAIClientError(
                f"Request to GraphQLAI API timed out after {DEFAULT_TIMEOUT}s. "
                "The API may be waking up from a cold start — please try again in a moment."
            )
        except requests.exceptions.ConnectionError as exc:
            raise GraphQLAIClientError(
                f"Could not reach the GraphQLAI API at {self.api_url}: {exc}"
            )
        except requests.exceptions.HTTPError as exc:
            raise GraphQLAIClientError(
                f"GraphQLAI API returned an error: {exc.response.status_code} {exc.response.reason}"
            )
        return response.json()

    @staticmethod
    def is_success(response: dict) -> bool:
        """Return True when the response contains a valid query and no validation errors."""
        return bool(response.get("graphql_query")) and not response.get("validation_errors")

    @staticmethod
    def extract_query(response: dict) -> str:
        """Return the best available query string from a response dict."""
        return response.get("graphql_query") or response.get("graphql_query_retry", "")
