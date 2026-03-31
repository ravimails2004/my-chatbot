"""
Azure DevOps REST API client.
Handles pipeline listing, triggering (with/without parameters), and status checks.
"""
import base64
import json
from typing import Any
import aiohttp

from config import Config


def _auth_header() -> dict[str, str]:
    token = base64.b64encode(f":{Config.ADO_PAT}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


async def list_pipelines(project: str | None = None) -> list[dict]:
    """Return all pipelines in the project."""
    project = project or Config.ADO_PROJECT
    url = f"{Config.ADO_BASE_URL}/{project}/_apis/pipelines?api-version=7.1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_auth_header()) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return [
                {"id": p["id"], "name": p["name"], "folder": p.get("folder", "\\")}
                for p in data.get("value", [])
            ]


async def get_pipeline(pipeline_id: int, project: str | None = None) -> dict:
    """Return details for a single pipeline."""
    project = project or Config.ADO_PROJECT
    url = f"{Config.ADO_BASE_URL}/{project}/_apis/pipelines/{pipeline_id}?api-version=7.1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_auth_header()) as resp:
            resp.raise_for_status()
            return await resp.json()


async def trigger_pipeline(
    pipeline_id: int,
    parameters: dict[str, Any] | None = None,
    branch: str = "main",
    project: str | None = None,
) -> dict:
    """
    Queue a pipeline run.

    Args:
        pipeline_id: Numeric pipeline ID.
        parameters: Optional dict of template/queue-time variables
                    e.g. {"environment": "staging", "runTests": "true"}
        branch: The source branch to run against (default: main).
        project: ADO project name (defaults to ADO_PROJECT env var).
    """
    project = project or Config.ADO_PROJECT
    url = f"{Config.ADO_BASE_URL}/{project}/_apis/pipelines/{pipeline_id}/runs?api-version=7.1"

    body: dict[str, Any] = {
        "resources": {
            "repositories": {
                "self": {"refName": f"refs/heads/{branch}"}
            }
        }
    }

    if parameters:
        body["templateParameters"] = parameters

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=_auth_header(), json=body) as resp:
            resp.raise_for_status()
            run = await resp.json()
            return {
                "run_id": run["id"],
                "name": run["name"],
                "state": run["state"],
                "url": run.get("_links", {}).get("web", {}).get("href", ""),
                "created_at": run.get("createdDate", ""),
            }


async def get_run_status(
    pipeline_id: int,
    run_id: int,
    project: str | None = None,
) -> dict:
    """Get the current state and result of a pipeline run."""
    project = project or Config.ADO_PROJECT
    url = (
        f"{Config.ADO_BASE_URL}/{project}/_apis/pipelines/{pipeline_id}"
        f"/runs/{run_id}?api-version=7.1"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_auth_header()) as resp:
            resp.raise_for_status()
            run = await resp.json()
            return {
                "run_id": run["id"],
                "name": run["name"],
                "state": run["state"],           # inProgress | completed | canceling
                "result": run.get("result", ""),  # succeeded | failed | canceled | (empty if running)
                "url": run.get("_links", {}).get("web", {}).get("href", ""),
                "finished_at": run.get("finishedDate", ""),
            }


async def get_recent_runs(
    pipeline_id: int,
    top: int = 5,
    project: str | None = None,
) -> list[dict]:
    """Return the N most recent runs for a pipeline."""
    project = project or Config.ADO_PROJECT
    url = (
        f"{Config.ADO_BASE_URL}/{project}/_apis/pipelines/{pipeline_id}"
        f"/runs?$top={top}&api-version=7.1"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_auth_header()) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return [
                {
                    "run_id": r["id"],
                    "name": r["name"],
                    "state": r["state"],
                    "result": r.get("result", ""),
                    "created_at": r.get("createdDate", ""),
                    "url": r.get("_links", {}).get("web", {}).get("href", ""),
                }
                for r in data.get("value", [])
            ]
