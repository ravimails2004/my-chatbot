# Teams Azure Pipelines Bot

A Microsoft Teams chatbot built in Python that triggers and monitors Azure Pipelines via keyword commands.

## Documentation

| Doc | Description |
|---|---|
| [Overview](docs/01-overview.md) | Architecture, request flow, tech stack |
| [Configuration](docs/02-configuration.md) | Environment variables and secrets |
| [Bot Commands](docs/03-bot-commands.md) | Full command reference with examples |
| [Code Reference](docs/04-code-reference.md) | Module-level code documentation |
| [Local Development](docs/05-local-development.md) | Running and testing locally with ngrok |
| [Docker](docs/06-docker.md) | Building and pushing the Docker image |
| [Kubernetes](docs/07-kubernetes.md) | EKS deployment, probes, rollout |
| [Azure Bot Setup](docs/08-azure-bot-setup.md) | One-time Azure Portal and Teams setup |
| [Troubleshooting](docs/09-troubleshooting.md) | Common errors and fixes |

---

## Project Structure

```
chatbot/
├── app/
│   ├── config.py          # All config loaded from environment variables
│   ├── azure_devops.py    # Azure DevOps REST API client
│   └── bot.py             # Bot command logic
├── app.py                 # aiohttp server (/api/messages + /health)
├── requirements.txt
├── Dockerfile
└── k8s/
    ├── secret.yaml        # Kubernetes secret (parameterised)
    ├── deployment.yaml    # Deployment (2 replicas)
    ├── service.yaml       # ClusterIP service
    └── ingress.yaml       # ALB ingress (HTTPS)
```

---

## Bot Commands

| Command | Description |
|---|---|
| `list` | List all pipelines with their IDs |
| `run <id_or_name>` | Trigger a pipeline on the `main` branch |
| `run <id_or_name> branch:<branch>` | Trigger on a specific branch |
| `run <id_or_name> branch:<branch> var:KEY=VALUE` | Trigger with pipeline variables |
| `status <pipeline_id> <run_id>` | Get the status of a pipeline run |
| `help` | Show available commands |

**Examples:**
```
run 42
run my-pipeline branch:develop
run my-pipeline branch:main var:ENV=staging var:DEPLOY=true
status 42 1001
```

---

## Environment Variables

All secrets are injected via environment variables — never hardcoded.

| Variable | Description |
|---|---|
| `MICROSOFT_APP_ID` | Bot's Microsoft App ID (from Azure Bot registration) |
| `MICROSOFT_APP_PASSWORD` | Bot's Microsoft App Password (client secret) |
| `AZURE_DEVOPS_ORG` | Azure DevOps organisation name |
| `AZURE_DEVOPS_PROJECT` | Azure DevOps project name |
| `AZURE_DEVOPS_PAT` | Azure DevOps Personal Access Token |
| `PORT` | Port to listen on (default: `3978`) |

---

## Deploy Steps

### 1. Register the Bot in Azure

1. Go to **Azure Portal** → search **Azure Bot** → Create
2. Choose **Multi Tenant** for channel type
3. Note the generated **App ID** and create an **App Password** (client secret) under the app registration
4. Set the **Messaging Endpoint** to:
   ```
   https://teams-bot.your-domain.com/api/messages
   ```
5. Under **Channels**, add the **Microsoft Teams** channel

---

### 2. Build and Push Docker Image to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name teams-bot

# Build image
docker build -t teams-bot .

# Tag and push
docker tag teams-bot:latest <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/teams-bot:latest

aws ecr get-login-password --region <REGION> | \
  docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com

docker push <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/teams-bot:latest
```

---

### 3. Configure Kubernetes Secrets

Edit `k8s/secret.yaml` and fill in your values:

```yaml
stringData:
  MICROSOFT_APP_ID: "your-microsoft-app-id"
  MICROSOFT_APP_PASSWORD: "your-microsoft-app-password"
  AZURE_DEVOPS_ORG: "your-org"
  AZURE_DEVOPS_PROJECT: "your-project"
  AZURE_DEVOPS_PAT: "your-pat"
```

> **Do not commit `secret.yaml` with real values.** Use AWS Secrets Manager + External Secrets Operator or Sealed Secrets for production.

Also update the image URI in `k8s/deployment.yaml`:
```yaml
image: <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/teams-bot:latest
```

---

### 4. Deploy to EKS

```bash
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

Verify the deployment:
```bash
kubectl get pods -l app=teams-bot
kubectl logs -l app=teams-bot
```

---

### 5. Ingress / TLS

`k8s/ingress.yaml` uses the **AWS Load Balancer Controller** with an ACM certificate.

Prerequisites:
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/) installed on your EKS cluster
- An ACM certificate for your domain — update the ARN in `ingress.yaml`:
  ```yaml
  alb.ingress.kubernetes.io/certificate-arn: "arn:aws:acm:<REGION>:<ACCOUNT>:certificate/<ID>"
  ```
- DNS record pointing `teams-bot.your-domain.com` to the ALB

Microsoft Bot Service requires **HTTPS** — the ALB terminates TLS and forwards HTTP to port 3978 inside the cluster.

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MICROSOFT_APP_ID=""
export MICROSOFT_APP_PASSWORD=""
export AZURE_DEVOPS_ORG="your-org"
export AZURE_DEVOPS_PROJECT="your-project"
export AZURE_DEVOPS_PAT="your-pat"

# Run the bot
python app.py
```

Use [ngrok](https://ngrok.com/) to expose the local server for Teams testing:
```bash
ngrok http 3978
# Set the ngrok HTTPS URL as the messaging endpoint in Azure Bot
```

---

## Azure DevOps PAT Permissions Required

When creating the PAT in Azure DevOps, grant the following scopes:

| Scope | Permission |
|---|---|
| Build | Read & Execute |
| Release | Read, write & Execute (if using classic releases) |
