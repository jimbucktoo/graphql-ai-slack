# GraphQLAI Slack

GraphQLAI Slack is a Slack integration that lets developers generate schema-compliant GraphQL queries from plain English directly inside Slack — no context switching required. Type `/graphql get all users with their name and email` and get a ready-to-use, formatted query back instantly. The app is a thin integration layer built on Slack Bolt that delegates all query generation to the existing [GraphQLAI API](https://graphql-ai-api.onrender.com), meaning it stays lightweight, schema-aware, and easy to deploy anywhere Python runs.

## Links

- [GraphQLAI Front-End](https://graphql-ai.surge.sh/) — GraphQLAI Front-End Application
- [GraphQLAI Back-End](https://graphql-ai-api.onrender.com) — GraphQLAI Back-End Server
- [GraphQLAI Repository](https://github.com/jimbucktoo/graphql-ai/) — GraphQLAI Github Repository
- [GraphQLAI API Repository](https://github.com/jimbucktoo/graphql-ai-api/) — GraphQLAI API Github Repository
- [GraphQLAI Slack Repository](https://github.com/jimbucktoo/graphqlai-slack/) — GraphQLAI Slack Github Repository

---

## Architecture

This app is a **pure integration layer** — it contains no query generation logic. All AI and schema-validation work happens inside the existing GraphQLAI API.

```
Slack
  │  /graphql <prompt>
  ▼
Bolt App (this repo)
  │  POST /query { prompt, endpoint }
  ▼
GraphQLAI API  (graphql-ai-api.onrender.com)
  │  prompt + schema introspection
  ▼
OpenAI
  │  generated query
  ▼
GraphQLAI API  (validates & optionally retries)
  │  { graphql_query, result }
  ▼
Bolt App → Block Kit response → Slack
```

### File structure

```
graphqlai-slack/
├── app.py                       # Entry point — wiring only
├── handlers/
│   ├── slash_commands.py        # /graphql command handler
│   └── workflows.py             # Workflow Builder step handler
├── services/
│   └── graphqlai_client.py      # HTTP client for the GraphQLAI API
├── utils/
│   └── block_kit.py             # Block Kit message formatters
├── tests/
│   ├── test_client.py
│   └── test_slash_command.py
├── .env.example
└── requirements.txt
```

---

## Prerequisites

- Python 3.10+
- A Slack workspace where you can create and install apps
- The GraphQLAI API already deployed (default: `https://graphql-ai-api.onrender.com`)

---

## Slack App Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App → From scratch**.
2. **Enable Socket Mode** under *Settings → Socket Mode*. Generate an **App-Level Token** with the `connections:write` scope — this is your `SLACK_APP_TOKEN` (`xapp-…`).
3. Under *Features → Slash Commands*, click **Create New Command**:
   - Command: `/graphql`
   - Short description: `Generate a GraphQL query from plain English`
   - Request URL: leave blank (Socket Mode handles routing)
4. Under *OAuth & Permissions → Scopes → Bot Token Scopes*, add:
   - `commands`
   - `chat:write`
   - `chat:write.public`
5. Under *Features → Workflow Steps*, enable **Workflow Steps** and add a step with callback ID `generate_graphql_query`.
6. Click **Install to Workspace** and copy the **Bot User OAuth Token** (`xoxb-…`) and the **Signing Secret** from *Basic Information*.

---

## Local Setup

```bash
git clone https://github.com/jimbucktoo/graphqlai-slack.git
cd graphqlai-slack
pip install -r requirements.txt
cp .env.example .env
# edit .env and fill in your tokens and GraphQL endpoint
```

---

## Running

```bash
python app.py
```

On startup you will see a log line confirming the registered commands and the API URL in use.

---

## Usage Examples

```
/graphql get all users with their name and email
/graphql find all posts with their title and author name
/graphql show comments on post with id 1
/graphql list all products with price and category
/graphql fetch the current user's profile and role
```

Each command returns a formatted, copy-paste-ready GraphQL query inside Slack. If the API cannot produce a valid query, it returns the best attempt along with the validation errors so you can rephrase and try again.

---

## Workflow Builder

The app registers a Workflow Step called **Generate GraphQL Query** (`generate_graphql_query`) that you can use inside Slack's no-code Workflow Builder:

1. Open **Workflow Builder** in your Slack workspace.
2. Create or edit a workflow and click **Add Step**.
3. Find **GraphQLAI** in the step list and select **Generate GraphQL Query**.
4. Enter a plain English description in the modal, e.g. *"get all orders placed in the last 7 days"*.
5. Save the step — the workflow will output two variables: `graphql_query` (the generated query string) and `original_prompt`.

You can pass these outputs into subsequent steps such as sending a message, updating a sheet, or calling a webhook.

---

## Deployment

Socket Mode works great for local development without a public URL. For production:

1. Replace `SocketModeHandler` with an HTTP adapter (e.g. `from slack_bolt.adapter.flask import SlackRequestHandler`).
2. Point your Slash Command's **Request URL** at your deployed server's `/slack/events` endpoint.
3. Deploy to **Render**, **Railway**, **Fly.io**, or any platform that supports Python. Set the environment variables listed in `.env.example` as secrets/config vars on your host.

---

## Technologies

- [Slack Bolt SDK](https://slack.dev/bolt-python/concepts) — Python framework for Slack apps
- [Slack Block Kit](https://api.slack.com/block-kit) — UI framework for rich Slack messages
- [requests](https://requests.readthedocs.io/) — HTTP client for the GraphQLAI API
- [python-dotenv](https://saurabh-kumar.com/python-dotenv/) — environment variable management

## Authors

- **James Liang** - *Initial work* - [jimbucktoo](https://github.com/jimbucktoo/)
