# Overview

## What Is This?

This is a Microsoft Teams chatbot that lets users trigger and monitor Azure Pipelines directly from a Teams conversation using simple text commands. No UI, no browser — just type a command in Teams and your pipeline runs.

## Architecture

```
Teams User
    │
    ▼  (HTTPS POST)
Microsoft Bot Service  ──── authenticates ──── Azure Active Directory
    │
    ▼  (forwards activity)
Bot Backend (EKS Pod)
    │  app.py  →  BotFrameworkAdapter  →  TeamsBot
    │
    ├── Command Parser  (bot.py)
    │
    └── Azure DevOps REST API  (azure_devops.py)
              └── dev.azure.com/{org}/{project}/_apis/pipelines
```

## Request Flow

1. User sends a message in Teams (e.g. `run my-pipeline branch:develop`)
2. Microsoft Bot Service authenticates the request and forwards it as an `Activity` to the bot's `/api/messages` endpoint
3. `BotFrameworkAdapter` in `app.py` validates the auth header and calls `TeamsBot.on_turn()`
4. `TeamsBot.on_message_activity()` in `bot.py` strips the `@mention` tag and routes to the matching command handler
5. The command handler calls `AzureDevOpsClient` in `azure_devops.py` which hits the Azure DevOps REST API using a PAT
6. The bot sends a formatted reply back to the Teams channel

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Web server | aiohttp |
| Bot framework | Microsoft Bot Framework SDK v4 (`botbuilder-core`) |
| Azure DevOps API | httpx (async HTTP client) |
| Container | Docker (python:3.12-slim) |
| Orchestration | Kubernetes on AWS EKS |
| Ingress / TLS | AWS Load Balancer Controller + ACM |
