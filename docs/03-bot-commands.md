# Bot Commands

All commands are sent as plain text messages to the bot in Microsoft Teams. The bot is case-insensitive and strips `@mention` tags automatically.

---

## `help`

Shows the list of available commands.

**Usage:**
```
help
```

Also triggered by `?` or sending an empty message.

---

## `list`

Lists all pipelines in the configured Azure DevOps project with their numeric IDs.

**Usage:**
```
list
```

**Example response:**
```
Available Pipelines:
- `12` — build-and-test
- `34` — deploy-staging
- `56` — deploy-production
```

---

## `run`

Triggers a pipeline. You can reference the pipeline by its numeric ID or by its exact name.

**Usage:**
```
run <pipeline_id_or_name>
run <pipeline_id_or_name> branch:<branch>
run <pipeline_id_or_name> branch:<branch> var:KEY=VALUE var:KEY2=VALUE2
```

| Argument | Required | Default | Description |
|---|---|---|---|
| `pipeline_id_or_name` | Yes | — | Numeric pipeline ID or exact pipeline name |
| `branch:<branch>` | No | `main` | Git branch to run the pipeline on |
| `var:KEY=VALUE` | No | — | Pipeline variables (repeatable) |

**Examples:**
```
run 34
run deploy-staging
run deploy-staging branch:develop
run deploy-staging branch:release/1.0 var:ENV=staging var:SKIP_TESTS=true
```

**Example response:**
```
Pipeline deploy-staging triggered on branch `develop`.
Run ID: `1042`
View run → https://dev.azure.com/...
```

**Name resolution:** If a name is provided instead of an ID, the bot calls `list` internally to find the matching pipeline. The match is case-insensitive.

---

## `status`

Gets the current state and result of a specific pipeline run.

**Usage:**
```
status <pipeline_id> <run_id>
```

| Argument | Description |
|---|---|
| `pipeline_id` | Numeric ID of the pipeline |
| `run_id` | Numeric ID of the run (returned when you triggered it) |

**Example:**
```
status 34 1042
```

**Example response:**
```
Pipeline deploy-staging | Run `1042`: **completed** (succeeded)
```

**Possible states from Azure DevOps:**

| State | Meaning |
|---|---|
| `inProgress` | Pipeline is currently running |
| `completed` | Pipeline finished (check result for success/failure) |
| `canceling` | Cancel was requested |

**Possible results:**

| Result | Meaning |
|---|---|
| `succeeded` | All steps passed |
| `failed` | One or more steps failed |
| `canceled` | Run was cancelled |
| `partiallySucceeded` | Some steps passed, some failed |

---

## Error Handling

If a command fails (network error, invalid pipeline, wrong PAT permissions), the bot replies with a plain-text error message describing what went wrong, e.g.:

```
Failed to trigger pipeline: 401 Unauthorized
Pipeline `bad-name` not found. Use `list` to see available pipelines.
```
