import re

from botbuilder.core import ActivityHandler, MessageFactory, TurnContext

from app.azure_devops import AzureDevOpsClient
from app.config import Config

HELP_TEXT = """**Azure Pipelines Bot — Commands:**

`list` — List all available pipelines
`run <pipeline_id_or_name>` — Trigger a pipeline on the default branch (main)
`run <pipeline_id_or_name> branch:<branch>` — Trigger on a specific branch
`run <pipeline_id_or_name> branch:<branch> var:KEY=VALUE` — Trigger with variables
`status <pipeline_id> <run_id>` — Get the status of a pipeline run
`help` — Show this message"""


class TeamsBot(ActivityHandler):
    def __init__(self):
        self._devops = AzureDevOpsClient(
            Config.AZURE_DEVOPS_ORG,
            Config.AZURE_DEVOPS_PROJECT,
            Config.AZURE_DEVOPS_PAT,
        )

    async def on_message_activity(self, turn_context: TurnContext):
        raw = turn_context.activity.text or ""
        # Strip bot @mention tags injected by Teams
        text = re.sub(r"<at>[^<]*</at>", "", raw).strip().lower()

        if text == "list":
            await self._handle_list(turn_context)
        elif text.startswith("run "):
            await self._handle_run(turn_context, text[4:].strip())
        elif text.startswith("status "):
            await self._handle_status(turn_context, text[7:].strip())
        elif text in ("help", "?", ""):
            await turn_context.send_activity(MessageFactory.text(HELP_TEXT))
        else:
            await turn_context.send_activity(
                MessageFactory.text("Unknown command. Type `help` to see available commands.")
            )

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------

    async def _handle_list(self, turn_context: TurnContext):
        try:
            pipelines = await self._devops.list_pipelines()
        except Exception as exc:
            await turn_context.send_activity(
                MessageFactory.text(f"Failed to list pipelines: {exc}")
            )
            return

        if not pipelines:
            await turn_context.send_activity(MessageFactory.text("No pipelines found."))
            return

        lines = ["**Available Pipelines:**"]
        for p in pipelines:
            lines.append(f"- `{p['id']}` — {p['name']}")
        await turn_context.send_activity(MessageFactory.text("\n".join(lines)))

    async def _handle_run(self, turn_context: TurnContext, args: str):
        parts = args.split()
        if not parts:
            await turn_context.send_activity(
                MessageFactory.text("Usage: `run <pipeline_id_or_name> [branch:<branch>] [var:KEY=VALUE ...]`")
            )
            return

        pipeline_ref = parts[0]
        branch = "main"
        variables: dict[str, str] = {}

        for part in parts[1:]:
            if part.startswith("branch:"):
                branch = part[len("branch:"):]
            elif part.startswith("var:") and "=" in part:
                key, value = part[len("var:"):].split("=", 1)
                variables[key] = value

        try:
            if pipeline_ref.isdigit():
                pipeline_id = int(pipeline_ref)
                pipeline_name = pipeline_ref
            else:
                pipelines = await self._devops.list_pipelines()
                match = next(
                    (p for p in pipelines if p["name"].lower() == pipeline_ref.lower()),
                    None,
                )
                if match is None:
                    await turn_context.send_activity(
                        MessageFactory.text(
                            f"Pipeline `{pipeline_ref}` not found. Use `list` to see available pipelines."
                        )
                    )
                    return
                pipeline_id = match["id"]
                pipeline_name = match["name"]

            run = await self._devops.trigger_pipeline(
                pipeline_id, branch, variables or None
            )
        except Exception as exc:
            await turn_context.send_activity(
                MessageFactory.text(f"Failed to trigger pipeline: {exc}")
            )
            return

        run_id = run.get("id")
        run_url = run.get("_links", {}).get("web", {}).get("href", "")
        msg = f"Pipeline **{pipeline_name}** triggered on branch `{branch}`.\nRun ID: `{run_id}`"
        if run_url:
            msg += f"\n[View run]({run_url})"
        await turn_context.send_activity(MessageFactory.text(msg))

    async def _handle_status(self, turn_context: TurnContext, args: str):
        parts = args.split()
        if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
            await turn_context.send_activity(
                MessageFactory.text("Usage: `status <pipeline_id> <run_id>`")
            )
            return

        pipeline_id, run_id = int(parts[0]), int(parts[1])
        try:
            run = await self._devops.get_run_status(pipeline_id, run_id)
        except Exception as exc:
            await turn_context.send_activity(
                MessageFactory.text(f"Failed to get run status: {exc}")
            )
            return

        state = run.get("state", "unknown")
        result = run.get("result", "")
        name = run.get("pipeline", {}).get("name", str(pipeline_id))
        msg = f"Pipeline **{name}** | Run `{run_id}`: **{state}**"
        if result:
            msg += f" ({result})"
        await turn_context.send_activity(MessageFactory.text(msg))
