# Troubleshooting

## Bot Does Not Respond in Teams

**Check pod status:**
```bash
kubectl get pods -l app=teams-bot
kubectl logs -l app=teams-bot
```

**Check ingress:**
```bash
kubectl get ingress teams-bot
# Confirm ADDRESS is populated (the ALB DNS name)
```

**Check messaging endpoint:**
- Azure Portal → Azure Bot → Configuration
- The endpoint must match the public URL exactly, including the path `/api/messages`
- Must be HTTPS

---

## `401 Unauthorized` When Triggering a Pipeline

The Azure DevOps PAT is invalid, expired, or lacks permissions.

- Regenerate the PAT at `https://dev.azure.com/{org}/_usersSettings/tokens`
- Ensure scopes include **Build → Read & Execute**
- Update the Kubernetes secret:
  ```bash
  kubectl create secret generic teams-bot-secret \
    --from-literal=AZURE_DEVOPS_PAT="new-pat" \
    --dry-run=client -o yaml | kubectl apply -f -
  ```
- Restart the pods to pick up the new secret:
  ```bash
  kubectl rollout restart deployment/teams-bot
  ```

---

## `Pipeline <name> not found`

- Run `list` to see the exact pipeline names in the project
- Pipeline name matching is case-insensitive but must be an exact match
- Confirm `AZURE_DEVOPS_ORG` and `AZURE_DEVOPS_PROJECT` point to the right project

---

## `Failed to trigger pipeline: ...` (Network Error)

The bot pod cannot reach `dev.azure.com`. Check:
- EKS node group security group allows outbound HTTPS (port 443)
- No restrictive network policies blocking egress from the `default` namespace

---

## Bot Replies with `Unknown command`

Teams injects an `<at>BotName</at>` mention tag at the start of messages when the bot is @mentioned in a channel. The bot strips this automatically using a regex. If the command is still not recognised:
- Make sure the command text comes **after** the @mention, e.g. `@PipelinesBot run 42`
- Try in a 1:1 chat with the bot where no mention tag is added

---

## Pods Crash-Looping

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name> --previous
```

Common causes:
- Missing required environment variable — check all five secrets are present in `teams-bot-secret`
- Invalid `PORT` value — must be a valid integer

---

## ACM Certificate Not Attaching to ALB

- The ARN in `ingress.yaml` must be in the same AWS region as the EKS cluster
- The certificate must be in `Issued` state (not pending validation)
- The AWS Load Balancer Controller must have the `elasticloadbalancing` and `acm` IAM permissions
