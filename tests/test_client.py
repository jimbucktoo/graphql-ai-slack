"""Tests for GraphQLAIClient."""

import unittest
from unittest.mock import MagicMock, patch

import requests

from services.graphqlai_client import (
    DEFAULT_TIMEOUT,
    GraphQLAIClient,
    GraphQLAIClientError,
)

API_URL = "https://graphql-ai-api.onrender.com"
GQL_ENDPOINT = "https://example.com/graphql"
PROMPT = "get all users with their name and email"


class TestGenerateQuery(unittest.TestCase):
    def _client(self) -> GraphQLAIClient:
        return GraphQLAIClient(api_url=API_URL, graphql_endpoint=GQL_ENDPOINT)

    def test_successful_response_parsing(self):
        payload = {"prompt": PROMPT, "graphql_query": "{ users { name email } }", "result": {}}
        mock_resp = MagicMock()
        mock_resp.json.return_value = payload
        mock_resp.raise_for_status = MagicMock()

        with patch("services.graphqlai_client.requests.post", return_value=mock_resp) as mock_post:
            result = self._client().generate_query(PROMPT)

        self.assertEqual(result, payload)
        mock_post.assert_called_once_with(
            f"{API_URL}/query",
            json={"prompt": PROMPT, "endpoint": GQL_ENDPOINT},
            timeout=DEFAULT_TIMEOUT,
        )

    def test_raises_on_http_error(self):
        mock_resp = MagicMock()
        http_err = requests.exceptions.HTTPError(response=MagicMock(status_code=500, reason="Internal Server Error"))
        mock_resp.raise_for_status.side_effect = http_err

        with patch("services.graphqlai_client.requests.post", return_value=mock_resp):
            with self.assertRaises(GraphQLAIClientError):
                self._client().generate_query(PROMPT)

    def test_raises_on_timeout(self):
        with patch(
            "services.graphqlai_client.requests.post",
            side_effect=requests.exceptions.Timeout,
        ):
            with self.assertRaises(GraphQLAIClientError) as ctx:
                self._client().generate_query(PROMPT)
        self.assertIn("timed out", str(ctx.exception))

    def test_raises_on_connection_error(self):
        with patch(
            "services.graphqlai_client.requests.post",
            side_effect=requests.exceptions.ConnectionError("unreachable"),
        ):
            with self.assertRaises(GraphQLAIClientError):
                self._client().generate_query(PROMPT)

    def test_timeout_value_is_passed_to_requests(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"graphql_query": "{ users { id } }"}
        mock_resp.raise_for_status = MagicMock()

        with patch("services.graphqlai_client.requests.post", return_value=mock_resp) as mock_post:
            self._client().generate_query(PROMPT)

        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["timeout"], DEFAULT_TIMEOUT)


class TestIsSuccess(unittest.TestCase):
    def test_returns_true_for_valid_response(self):
        self.assertTrue(
            GraphQLAIClient.is_success({"graphql_query": "{ users { id } }"})
        )

    def test_returns_false_when_validation_errors_present(self):
        self.assertFalse(
            GraphQLAIClient.is_success(
                {
                    "graphql_query_attempted": "{ users { bad_field } }",
                    "validation_errors": ["Field 'bad_field' does not exist"],
                }
            )
        )

    def test_returns_false_when_graphql_query_missing(self):
        self.assertFalse(GraphQLAIClient.is_success({}))

    def test_returns_false_when_both_query_and_errors(self):
        self.assertFalse(
            GraphQLAIClient.is_success(
                {"graphql_query": "{ users { id } }", "validation_errors": ["some error"]}
            )
        )


class TestExtractQuery(unittest.TestCase):
    def test_prefers_graphql_query(self):
        resp = {"graphql_query": "{ users { id } }", "graphql_query_retry": "{ users { name } }"}
        self.assertEqual(GraphQLAIClient.extract_query(resp), "{ users { id } }")

    def test_falls_back_to_retry_query(self):
        resp = {"graphql_query_retry": "{ users { name } }"}
        self.assertEqual(GraphQLAIClient.extract_query(resp), "{ users { name } }")

    def test_returns_empty_string_when_neither_present(self):
        self.assertEqual(GraphQLAIClient.extract_query({}), "")


if __name__ == "__main__":
    unittest.main()
