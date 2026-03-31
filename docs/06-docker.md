# Docker

## Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3978

CMD ["python", "app.py"]
```

- Base image: `python:3.12-slim` — minimal footprint, no unnecessary system packages
- Dependencies are installed before copying source code so Docker can cache the layer
- The app listens on port `3978` (configurable via the `PORT` env var)

## Build

```bash
docker build -t teams-bot .
```

## Run Locally

```bash
docker run --rm \
  -p 3978:3978 \
  -e MICROSOFT_APP_ID="your-app-id" \
  -e MICROSOFT_APP_PASSWORD="your-app-password" \
  -e AZURE_DEVOPS_ORG="your-org" \
  -e AZURE_DEVOPS_PROJECT="your-project" \
  -e AZURE_DEVOPS_PAT="your-pat" \
  teams-bot
```

## Push to AWS ECR

**1. Create the ECR repository (one-time)**

```bash
aws ecr create-repository --repository-name teams-bot --region <REGION>
```

**2. Authenticate Docker to ECR**

```bash
aws ecr get-login-password --region <REGION> | \
  docker login --username AWS --password-stdin \
  <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com
```

**3. Tag and push**

```bash
docker tag teams-bot:latest \
  <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/teams-bot:latest

docker push <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/teams-bot:latest
```

**4. Update the image URI in `k8s/deployment.yaml`**

```yaml
image: <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/teams-bot:latest
```

## Image Tagging Strategy

For production, tag images with the Git commit SHA instead of `latest` to make rollbacks predictable:

```bash
TAG=$(git rev-parse --short HEAD)
docker tag teams-bot:latest \
  <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/teams-bot:$TAG

docker push <AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/teams-bot:$TAG
```

Then reference the exact tag in `deployment.yaml`.
