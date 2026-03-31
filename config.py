import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]

    ADO_ORGANIZATION: str = os.environ["ADO_ORGANIZATION"]
    ADO_PROJECT: str = os.environ["ADO_PROJECT"]
    ADO_PAT: str = os.environ["ADO_PAT"]
    ADO_BASE_URL: str = f"https://dev.azure.com/{os.environ.get('ADO_ORGANIZATION', '')}"

    MICROSOFT_APP_ID: str = os.getenv("MICROSOFT_APP_ID", "")
    MICROSOFT_APP_PASSWORD: str = os.getenv("MICROSOFT_APP_PASSWORD", "")

    PORT: int = int(os.getenv("PORT", "3978"))
