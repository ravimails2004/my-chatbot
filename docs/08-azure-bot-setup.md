# Azure Bot Setup

This page covers the one-time setup required in the Azure Portal and Microsoft Teams to connect the bot.

---

## 1. Create an Azure Bot

1. Go to the [Azure Portal](https://portal.azure.com)
2. Search for **Azure Bot** and click **Create**
3. Fill in:
   - **Bot handle** — unique name (e.g. `teams-pipelines-bot`)
   - **Subscription / Resource group** — choose or create one
   - **Pricing tier** — `F0` (free) is fine for most use cases
   - **Microsoft App ID** — select **Create new Microsoft App ID**
4. Click **Review + Create** → **Create**

---

## 2. Get App ID and Create a Client Secret

1. After the bot is created, open the resource and go to **Configuration**
2. Note the **Microsoft App ID** — you need this for `MICROSOFT_APP_ID`
3. Click **Manage** next to the App ID — this opens the App Registration in AAD
4. Go to **Certificates & secrets** → **New client secret**
5. Set an expiry and click **Add**
6. Copy the secret **Value** immediately (it won't be shown again) — this is `MICROSOFT_APP_PASSWORD`

---

## 3. Set the Messaging Endpoint

1. Back in the Azure Bot resource → **Configuration**
2. Set **Messaging endpoint** to:
   ```
   https://teams-bot.your-domain.com/api/messages
   ```
   This must be your public HTTPS URL — the ALB hostname or your custom domain from the Ingress.
3. Click **Apply**

---

## 4. Enable the Microsoft Teams Channel

1. In the Azure Bot resource → **Channels**
2. Click **Microsoft Teams**
3. Accept the terms and click **Apply**

---

## 5. Add the Bot to a Teams Channel or Chat

**Option A — Install from App Studio / Developer Portal:**

1. Open [Teams Developer Portal](https://dev.teams.microsoft.com/)
2. Go to **Apps** → **New app**
3. Fill in app details (name, description, icons)
4. Under **App features** → **Bot** → select your registered bot App ID
5. Set the scope: `Personal`, `Team`, or `Group chat` as needed
6. **Publish** → **Publish to your org** (or sideload for testing)

**Option B — Direct install via App ID (for testing):**

In Teams, go to **Apps** → **Upload a custom app** and upload the app manifest zip.

---

## 6. Verify the Connection

Send `help` to the bot in Teams. If everything is configured correctly, you should receive the list of available commands.

If the bot does not respond:
- Check pod logs: `kubectl logs -l app=teams-bot`
- Verify the messaging endpoint URL in Azure Bot Configuration
- Confirm the ALB is reachable and the ACM cert is valid
- Confirm `MICROSOFT_APP_ID` and `MICROSOFT_APP_PASSWORD` match the Azure registration
