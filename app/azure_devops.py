import base64
from typing import Optional

import httpx


class AzureDevOpsClient:
    def __init__(self, org: str, project: str, pat: str):
        self.org = org
        self.project = project
        self.base_url = f"https://dev.azure.com/{org}/{project}/_apis"
        token = base64.b64encode(f":{pat}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

    async def list_pipelines(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/pipelines?api-version=7.0",
                headers=self.headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("value", [])

    async def trigger_pipeline(
        self,
        pipeline_id: int,
        branch: str = "main",
        variables: Optional[dict] = None,
    ) -> dict:
        body: dict = {
            "resources": {
                "repositories": {
                    "self": {"refName": f"refs/heads/{branch}"}
                }
            }
        }
        if variables:
            body["variables"] = {k: {"value": v} for k, v in variables.items()}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/pipelines/{pipeline_id}/runs?api-version=7.0",
                headers=self.headers,
                json=body,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_run_status(self, pipeline_id: int, run_id: int) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/pipelines/{pipeline_id}/runs/{run_id}?api-version=7.0",
                headers=self.headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
