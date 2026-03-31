# Code Reference

## Module Map

```
chatbot/
├── app.py                 # Entry point — HTTP server and route definitions
└── app/
    ├── config.py          # Environment variable loading
    ├── azure_devops.py    # Azure DevOps REST API client
    └── bot.py             # Bot activity handler and command routing
```

---

## `app.py` — Entry Point

Starts the `aiohttp` web server and wires up the Bot Framework adapter.

### Routes

| Method | Path | Handler | Description |
|---|---|---|---|
| `POST` | `/api/messages` | `messages()` | Receives all incoming Teams activities |
| `GET` | `/health` | `health()` | Liveness/readiness probe endpoint |

### Key objects

- **`adapter`** — `BotFrameworkAdapter` instance. Validates the JWT auth header on every incoming request using `MICROSOFT_APP_ID` and `MICROSOFT_APP_PASSWORD`.
- **`bot`** — singleton `TeamsBot` instance. Shared across all requests.

### `messages(req)` flow

```
POST /api/messages
  └── deserialize JSON body → Activity
  └── adapter.process_activity(activity, auth_header, callback)
        └── validates JWT
        └── calls callback → bot.on_turn(turn_context)
```

---

## `app/config.py` — Configuration

Simple class that reads all values from environment variables at import time. No instances needed — access values as class attributes:

```python
from app.config import Config
Config.AZURE_DEVOPS_PAT  # str
Config.PORT              # int
```

---

## `app/azure_devops.py` — Azure DevOps Client

### `AzureDevOpsClient(org, project, pat)`

Async HTTP client wrapping the Azure DevOps Pipelines REST API (`api-version=7.0`).

Authentication uses HTTP Basic Auth with the PAT: the PAT is Base64-encoded as `:{pat}` and sent in the `Authorization` header on every request.

#### Methods

---

**`list_pipelines() → list[dict]`**

```
GET https://dev.azure.com/{org}/{project}/_apis/pipelines?api-version=7.0
```

Returns a list of pipeline objects. Each object contains at minimum:
- `id` — numeric pipeline ID
- `name` — pipeline display name

Timeout: 10s.

---

**`trigger_pipeline(pipeline_id, branch="main", variables=None) → dict`**

```
POST https://dev.azure.com/{org}/{project}/_apis/pipelines/{id}/runs?api-version=7.0
```

Request body:
```json
{
  "resources": {
    "repositories": {
      "self": { "refName": "refs/heads/<branch>" }
    }
  },
  "variables": {
    "KEY": { "value": "VALUE" }
  }
}
```

Returns the created run object. Key fields in the response:
- `id` — run ID
- `state` — initial state (usually `inProgress`)
- `_links.web.href` — direct URL to the run in Azure DevOps

Timeout: 15s.

---

**`get_run_status(pipeline_id, run_id) → dict`**

```
GET https://dev.azure.com/{org}/{project}/_apis/pipelines/{id}/runs/{run_id}?api-version=7.0
```

Returns the run object with current `state` and `result` fields.

Timeout: 10s.

---

## `app/bot.py` — Bot Logic

### `TeamsBot(ActivityHandler)`

Handles incoming messages from Teams.

#### `on_message_activity(turn_context)`

Entry point for all text messages. Strips `<at>...</at>` mention tags (injected by Teams when the bot is @mentioned) then routes on the lowercased text:

| Text pattern | Handler |
|---|---|
| `list` | `_handle_list()` |
| `run ...` | `_handle_run()` |
| `status ...` | `_handle_status()` |
| `help` / `?` / empty | sends `HELP_TEXT` |
| anything else | "Unknown command" message |

#### `_handle_list(turn_context)`

Calls `AzureDevOpsClient.list_pipelines()` and formats results as a markdown list.

#### `_handle_run(turn_context, args)`

Parses `args` for:
- `pipeline_ref` — first token (ID or name)
- `branch:<value>` tokens
- `var:KEY=VALUE` tokens (multiple allowed)

If `pipeline_ref` is not numeric, resolves it to an ID by calling `list_pipelines()` and matching on name (case-insensitive).

Calls `AzureDevOpsClient.trigger_pipeline()` and replies with the run ID and a link to the run.

#### `_handle_status(turn_context, args)`

Expects two numeric tokens: `pipeline_id` and `run_id`. Calls `AzureDevOpsClient.get_run_status()` and formats the `state` and `result`.
