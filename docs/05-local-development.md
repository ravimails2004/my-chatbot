# Local Development

## Prerequisites

- Python 3.12+
- An Azure Bot registration (App ID + App Password)
- An Azure DevOps PAT
- [ngrok](https://ngrok.com/) (to expose the local server to Microsoft Bot Service)

## Setup

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Set environment variables**

```bash
export MICROSOFT_APP_ID="your-app-id"
export MICROSOFT_APP_PASSWORD="your-app-password"
export AZURE_DEVOPS_ORG="your-org"
export AZURE_DEVOPS_PROJECT="your-project"
export AZURE_DEVOPS_PAT="your-pat"
```

Or create a `.env` file and source it:

```bash
# .env  (do NOT commit this file)
MICROSOFT_APP_ID=your-app-id
MICROSOFT_APP_PASSWORD=your-app-password
AZURE_DEVOPS_ORG=your-org
AZURE_DEVOPS_PROJECT=your-project
AZURE_DEVOPS_PAT=your-pat
```
```bash
source .env
```

**3. Run the server**

```bash
python app.py
```

The server starts on `http://0.0.0.0:3978`.

## Exposing the Server with ngrok

Microsoft Bot Service must be able to reach your local machine over HTTPS. Use ngrok to create a public tunnel:

```bash
ngrok http 3978
```

ngrok will print a public URL like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:3978
```

**4. Update the messaging endpoint in Azure Bot**

Go to Azure Portal → your Azure Bot → Configuration → set:
```
Messaging endpoint: https://abc123.ngrok.io/api/messages
```

You can now test the bot in Microsoft Teams.

## Health Check

```bash
curl http://localhost:3978/health
# → ok
```

## Testing Without Teams

You can send a raw POST to `/api/messages` to simulate an activity during development. Note: the Bot Framework adapter will reject requests with an invalid or missing auth header unless `MICROSOFT_APP_ID` is left empty (which disables auth validation):

```bash
# Only works when MICROSOFT_APP_ID is empty (no-auth mode)
curl -X POST http://localhost:3978/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "type": "message",
    "text": "list",
    "from": {"id": "test-user"},
    "conversation": {"id": "test-conv"},
    "channelId": "test",
    "serviceUrl": "http://localhost"
  }'
```
