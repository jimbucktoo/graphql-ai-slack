"""Tests for the /graphql slash command handler."""

import unittest
from unittest.mock import MagicMock

from services.graphqlai_client import GraphQLAIClientError


def _invoke(text: str, client: MagicMock) -> tuple[MagicMock, MagicMock]:
    """Extract and call the registered slash command handler directly.

    Uses a fake app shim to capture the handler closure without starting Bolt.
    """
    from handlers.slash_commands import register_slash_commands

    recorded: dict = {}

    class _FakeApp:
        def command(self, name: str):
            def deco(fn):
                recorded["fn"] = fn
                return fn
            return deco

    register_slash_commands(_FakeApp(), client)

    ack = MagicMock()
    respond = MagicMock()
    body = {"text": text, "command": "/graphql"}
    recorded["fn"](ack=ack, body=body, respond=respond)
    return ack, respond


class TestSlashCommandAck(unittest.TestCase):
    def test_ack_called_for_empty_input(self):
        client = MagicMock()
        ack, _ = _invoke("", client)
        ack.assert_called_once()

    def test_ack_called_for_valid_input(self):
        client = MagicMock()
        client.generate_query.return_value = {"graphql_query": "{ users { id } }"}
        client.is_success.return_value = True
        client.extract_query.return_value = "{ users { id } }"
        ack, _ = _invoke("get all users", client)
        ack.assert_called_once()

    def test_usage_message_returned_for_empty_input(self):
        client = MagicMock()
        _, respond = _invoke("", client)
        respond.assert_called_once()
        call_kwargs = respond.call_args.kwargs
        self.assertIn("blocks", call_kwargs)
        header = call_kwargs["blocks"][0]
        self.assertEqual(header["type"], "header")
        self.assertIn("GraphQLAI", header["text"]["text"])

    def test_success_response_structure(self):
        client = MagicMock()
        client.generate_query.return_value = {"graphql_query": "{ users { id name } }"}
        client.is_success.return_value = True
        client.extract_query.return_value = "{ users { id name } }"
        _, respond = _invoke("get all users with id and name", client)
        call_kwargs = respond.call_args.kwargs
        blocks = call_kwargs["blocks"]
        self.assertEqual(blocks[0]["type"], "header")
        self.assertIn("GraphQLAI", blocks[0]["text"]["text"])
        all_text = " ".join(
            b.get("text", {}).get("text", "")
            for b in blocks
            if b.get("type") == "section"
        )
        self.assertIn("{ users { id name } }", all_text)

    def test_error_response_on_client_error(self):
        client = MagicMock()
        client.generate_query.side_effect = GraphQLAIClientError("Connection refused")
        _, respond = _invoke("get all users", client)
        call_kwargs = respond.call_args.kwargs
        blocks = call_kwargs["blocks"]
        header_text = blocks[0]["text"]["text"]
        self.assertIn("Error", header_text)

    def test_validation_error_response_structure(self):
        client = MagicMock()
        client.generate_query.return_value = {
            "graphql_query_attempted": "{ users { bad_field } }",
            "graphql_query_retry": "{ users { bad_field } }",
            "validation_errors": ["Field 'bad_field' does not exist on type 'User'"],
        }
        client.is_success.return_value = False
        client.extract_query.return_value = "{ users { bad_field } }"
        _, respond = _invoke("get all users with bad field", client)
        call_kwargs = respond.call_args.kwargs
        blocks = call_kwargs["blocks"]
        header_text = blocks[0]["text"]["text"]
        self.assertIn("Validation", header_text)


if __name__ == "__main__":
    unittest.main()
