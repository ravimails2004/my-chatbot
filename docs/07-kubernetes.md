# Kubernetes (EKS)

## Manifest Overview

| File | Kind | Purpose |
|---|---|---|
| `k8s/secret.yaml` | `Secret` | Stores all sensitive config values |
| `k8s/deployment.yaml` | `Deployment` | Runs 2 bot pod replicas |
| `k8s/service.yaml` | `Service` | ClusterIP — internal load balancing |
| `k8s/ingress.yaml` | `Ingress` | ALB — exposes `/api/messages` over HTTPS |

---

## Secret

`k8s/secret.yaml` uses `stringData` so values are stored as plain strings (Kubernetes Base64-encodes them automatically):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: teams-bot-secret
  namespace: default
type: Opaque
stringData:
  MICROSOFT_APP_ID: "..."
  MICROSOFT_APP_PASSWORD: "..."
  AZURE_DEVOPS_ORG: "..."
  AZURE_DEVOPS_PROJECT: "..."
  AZURE_DEVOPS_PAT: "..."
```

> Do not commit this file with real values. See the [Configuration](02-configuration.md) page for production secret management options.

---

## Deployment

Key settings in `k8s/deployment.yaml`:

| Setting | Value | Reason |
|---|---|---|
| `replicas` | `2` | High availability — one pod can restart without downtime |
| `containerPort` | `3978` | Must match the port the app listens on |
| `resources.requests` | `128Mi` / `100m` | Minimum guaranteed resources per pod |
| `resources.limits` | `256Mi` / `250m` | Cap to prevent runaway memory usage |

### Health Probes

Both probes hit `GET /health` which returns `200 ok`:

- **`livenessProbe`** — if this fails, Kubernetes restarts the pod (`initialDelaySeconds: 10`, `periodSeconds: 30`)
- **`readinessProbe`** — if this fails, the pod is removed from the Service endpoints until it recovers (`initialDelaySeconds: 5`, `periodSeconds: 10`)

---

## Service

`k8s/service.yaml` creates a `ClusterIP` service that load-balances across all healthy pods on port `80` → `3978`:

```yaml
ports:
  - protocol: TCP
    port: 80
    targetPort: 3978
type: ClusterIP
```

The service is internal only — external traffic comes through the Ingress.

---

## Ingress

`k8s/ingress.yaml` uses the **AWS Load Balancer Controller** to provision an internet-facing Application Load Balancer.

**Prerequisites:**
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/) installed in the cluster
- An ACM certificate for your domain
- A DNS record pointing your domain to the ALB

**Key annotations:**

| Annotation | Value | Purpose |
|---|---|---|
| `alb.ingress.kubernetes.io/scheme` | `internet-facing` | Public ALB |
| `alb.ingress.kubernetes.io/target-type` | `ip` | Routes directly to pod IPs |
| `alb.ingress.kubernetes.io/listen-ports` | `[{"HTTPS": 443}]` | HTTPS only (required by Bot Service) |
| `alb.ingress.kubernetes.io/certificate-arn` | your ACM ARN | TLS certificate |

Only `/api/messages` is exposed — the `/health` endpoint is only accessible internally within the cluster.

---

## Deploy

```bash
# Apply in order (secret must exist before deployment)
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

## Verify

```bash
# Check pods are running
kubectl get pods -l app=teams-bot

# Stream logs
kubectl logs -l app=teams-bot -f

# Check ingress and get ALB hostname
kubectl get ingress teams-bot
```

## Update / Redeploy

After pushing a new image to ECR:

```bash
kubectl set image deployment/teams-bot \
  teams-bot=<AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/teams-bot:<NEW_TAG>
```

Kubernetes performs a rolling update — old pods stay up until new pods are healthy.

## Rollback

```bash
kubectl rollout undo deployment/teams-bot
```
