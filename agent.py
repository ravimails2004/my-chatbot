"""
Claude AI agent with Azure DevOps tools.

Uses the Anthropic beta tool runner so the agent loop (call → execute tool →
feed result back → repeat) is handled automatically.
"""
import json
from anthropic import AsyncAnthropic, beta_async_tool

import ado_client
from config import Config

client = AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """\
You are an Azure DevOps Pipeline Assistant integrated into Microsoft Teams.
You help users manage and trigger CI/CD pipelines using natural language.

You have access to the following tools:
- list_pipelines: List all available pipelines
- get_pipeline_details: Get info about a specific pipeline
- trigger_pipeline: Run a pipeline (with or without parameters)
- get_run_status: Check the status of a pipeline run
- get_recent_runs: View recent run history for a pipeline

Guidelines:
- Be concise and friendly — this is a chat interface.
- When triggering a pipeline, confirm the pipeline name and parameters before proceeding.
- Format run URLs as clickable markdown links.
- If the user asks to run a pipeline by name, first list pipelines to find the correct ID.
- Always report the run URL so the user can track progress in Azure DevOps.
- If parameters are required but not provided, ask the user for them.
"""


# ── Tool definitions ──────────────────────────────────────────────────────────

@beta_async_tool
async def list_pipelines(project: str = "") -> str:
    """
    List all pipelines in the Azure DevOps project.

    Args:
        project: Optional ADO project name. Defaults to the configured project.
    """
    pipelines = await ado_client.list_pipelines(project or None)
    if not pipelines:
        return "No pipelines found."
    lines = [f"• [{p['name']}] (ID: {p['id']}, Folder: {p['folder']})" for p in pipelines]
    return "\n".join(lines)


@beta_async_tool
async def get_pipeline_details(pipeline_id: int, project: str = "") -> str:
    """
    Get details for a specific pipeline by its numeric ID.

    Args:
        pipeline_id: The numeric ID of the pipeline.
        project: Optional ADO project name.
    """
    pipeline = await ado_client.get_pipeline(pipeline_id, project or None)
    return json.dumps(pipeline, indent=2)


@beta_async_tool
async def trigger_pipeline(
    pipeline_id: int,
    branch: str = "main",
    parameters: str = "",
    project: str = "",
) -> str:
    """
    Trigger (queue) a pipeline run.

    Args:
        pipeline_id: Numeric ID of the pipeline to run.
        branch: Source branch to run against (default: main).
        parameters: JSON string of template parameters e.g. '{"env": "staging"}'.
                    Pass empty string if no parameters are needed.
        project: Optional ADO project name.
    """
    params_dict = None
    if parameters.strip():
        try:
            params_dict = json.loads(parameters)
        except json.JSONDecodeError:
            return "Error: parameters must be valid JSON, e.g. '{\"key\": \"value\"}'."

    run = await ado_client.trigger_pipeline(
        pipeline_id=pipeline_id,
        parameters=params_dict,
        branch=branch,
        project=project or None,
    )
    url = run.get("url", "")
    link = f"[View run #{run['run_id']}]({url})" if url else f"Run #{run['run_id']}"
    return (
        f"Pipeline triggered successfully!\n"
        f"- Run ID: {run['run_id']}\n"
        f"- Name: {run['name']}\n"
        f"- State: {run['state']}\n"
        f"- Branch: {branch}\n"
        f"- {link}"
    )


@beta_async_tool
async def get_run_status(pipeline_id: int, run_id: int, project: str = "") -> str:
    """
    Get the current status and result of a pipeline run.

    Args:
        pipeline_id: Numeric ID of the pipeline.
        run_id: Numeric ID of the specific run to check.
        project: Optional ADO project name.
    """
    status = await ado_client.get_run_status(pipeline_id, run_id, project or None)
    url = status.get("url", "")
    link = f"[Open in Azure DevOps]({url})" if url else ""
    result_line = f"- Result: {status['result']}" if status.get("result") else ""
    finished = f"- Finished: {status['finished_at']}" if status.get("finished_at") else ""
    parts = [
        f"Run #{run_id} status:",
        f"- State: {status['state']}",
        result_line,
        finished,
        link,
    ]
    return "\n".join(p for p in parts if p)


@beta_async_tool
async def get_recent_runs(pipeline_id: int, top: int = 5, project: str = "") -> str:
    """
    Get the most recent runs for a pipeline.

    Args:
        pipeline_id: Numeric ID of the pipeline.
        top: Number of recent runs to return (default: 5, max: 20).
        project: Optional ADO project name.
    """
    top = min(top, 20)
    runs = await ado_client.get_recent_runs(pipeline_id, top, project or None)
    if not runs:
        return "No runs found for this pipeline."
    lines = []
    for r in runs:
        state = r["state"]
        result = f" ({r['result']})" if r.get("result") else ""
        url = r.get("url", "")
        link = f" — [View]({url})" if url else ""
        lines.append(f"• Run #{r['run_id']}: {state}{result} — {r['created_at']}{link}")
    return "\n".join(lines)


# ── Agent entry point ─────────────────────────────────────────────────────────

TOOLS = [list_pipelines, get_pipeline_details, trigger_pipeline, get_run_status, get_recent_runs]


async def run_agent(user_message: str, conversation_history: list[dict] | None = None) -> str:
    """
    Run the Claude agent for a single user turn.

    Args:
        user_message: The latest message from the Teams user.
        conversation_history: Prior turns (list of {role, content} dicts).
                              Pass None for single-turn / stateless usage.

    Returns:
        The assistant's final text response.
    """
    messages = list(conversation_history or [])
    messages.append({"role": "user", "content": user_message})

    final_text = ""
    async for message in client.beta.messages.tool_runner(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=messages,
    ):
        # Each yielded message is a BetaMessage; collect the last text content
        for block in message.content:
            if block.type == "text":
                final_text = block.text

    return final_text or "I'm sorry, I couldn't generate a response. Please try again."
