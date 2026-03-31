# Configuration

All configuration is loaded at startup from environment variables. There are no config files — secrets are injected at runtime via Kubernetes Secrets.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `MICROSOFT_APP_ID` | Yes | — | Microsoft App ID from the Azure Bot registration |
| `MICROSOFT_APP_PASSWORD` | Yes | — | Client secret for the App ID |
| `AZURE_DEVOPS_ORG` | Yes | — | Azure DevOps organisation name (e.g. `mycompany`) |
| `AZURE_DEVOPS_PROJECT` | Yes | — | Azure DevOps project name (e.g. `backend`) |
| `AZURE_DEVOPS_PAT` | Yes | — | Personal Access Token with pipeline execute permissions |
| `PORT` | No | `3978` | Port the aiohttp server listens on |

## Where Config Is Loaded

`app/config.py` reads all values from the environment:

```python
class Config:
    MICROSOFT_APP_ID: str = os.environ.get("MICROSOFT_APP_ID", "")
    MICROSOFT_APP_PASSWORD: str = os.environ.get("MICROSOFT_APP_PASSWORD", "")
    AZURE_DEVOPS_ORG: str = os.environ.get("AZURE_DEVOPS_ORG", "")
    AZURE_DEVOPS_PROJECT: str = os.environ.get("AZURE_DEVOPS_PROJECT", "")
    AZURE_DEVOPS_PAT: str = os.environ.get("AZURE_DEVOPS_PAT", "")
    PORT: int = int(os.environ.get("PORT", 3978))
```

`Config` is imported directly in `app.py` (for the Bot Framework adapter) and in `app/bot.py` (for the Azure DevOps client).

## Kubernetes Secrets

In EKS, all values are stored in a Kubernetes `Secret` (`k8s/secret.yaml`) and mapped to container environment variables in the `Deployment`:

```yaml
env:
  - name: AZURE_DEVOPS_PAT
    valueFrom:
      secretKeyRef:
        name: teams-bot-secret
        key: AZURE_DEVOPS_PAT
```

> **Security note:** Do not commit `k8s/secret.yaml` with real values. In production, use [AWS Secrets Manager with External Secrets Operator](https://external-secrets.io/) or [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) to manage secrets safely in Git.

## Azure DevOps PAT Permissions

When creating the PAT at `https://dev.azure.com/{org}/_usersSettings/tokens`, grant only the minimum required scopes:

| Scope | Permission |
|---|---|
| Build | Read & Execute |
| Release | Read, write & Execute *(only if using classic release pipelines)* |
