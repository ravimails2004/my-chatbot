import os


class Config:
    MICROSOFT_APP_ID: str = os.environ.get("MICROSOFT_APP_ID", "")
    MICROSOFT_APP_PASSWORD: str = os.environ.get("MICROSOFT_APP_PASSWORD", "")
    AZURE_DEVOPS_ORG: str = os.environ.get("AZURE_DEVOPS_ORG", "")
    AZURE_DEVOPS_PROJECT: str = os.environ.get("AZURE_DEVOPS_PROJECT", "")
    AZURE_DEVOPS_PAT: str = os.environ.get("AZURE_DEVOPS_PAT", "")
    PORT: int = int(os.environ.get("PORT", 3978))
