# Cloudflare Access IP Auto-Updater

[![deepwiki-badge](https://deepwiki.com/badge.svg)](https://deepwiki.com/Mouchoir/cloudflare-allow-my-ip)

## 🌐 Goal

This app automatically updates your public IP in a [Cloudflare Zero Trust Access Policy](https://dash.teams.cloudflare.com/) to whitelist your current IP for bypass access (e.g., no OTP when at home).

It is designed to run:

* Once via CLI or script
* Or continuously via Docker with scheduled checks (e.g., every 15 min)

## ✅ Features

* Automatically fetches current public IP
* Checks if it's already set in a reusable Access policy
* Updates the policy with your IP if it has changed

---

## 🤩 Setup

### 1. ⚙️ Create a Reusable Cloudflare Access Policy

1. Go to the [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Select your account (top left corner)
3. Navigate to **Access** → **Policies**
4. Click **Create Access Policy**
5. Set action: `Bypass`
6. Under **Include**, add an IP rule with your current public IP (e.g., `85.11.244.50/32`)
7. Save and assign to your application

💡 You can find your current IP at [https://api.ipify.org/](https://api.ipify.org/)

### 2. 🔐 Create an API Token

1. Visit [API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Click **Create Token** → **Custom Token**
3. Permissions:

   * `Access: Policies` (Edit) under **Account** scope
4. Save your token securely

---

## ⚙️ Configure Your `.env` File

Create a `.env` file in the project root with:

```env
CF_API_TOKEN=your_cloudflare_token
CF_ACCOUNT_ID=your_account_id
CF_ACCESS_POLICY_ID=your_policy_id
```

* `CF_API_TOKEN`: Your API token from Cloudflare's dashboard
* `CF_ACCOUNT_ID`: Found in any API URL or your account overview
* `CF_ACCESS_POLICY_ID`: Get this from the Access policy URL (e.g., `/access/policies/{policy_id}`)

---

## 🥪 Local Development

### Install

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

### Ignore sensitive files

Ensure your `.gitignore` includes:

```gitignore
.env
.venv/
__pycache__/
```

---

## 🐳 Docker Setup

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### docker-compose.yml

```yaml
version: "3.8"
services:
  cf-ip-updater:
    build: .
    container_name: cf-ip-updater
    restart: unless-stopped
    env_file: .env
```

> ❗ Docker does not automatically rerun scripts. Use restart policies or schedule the container via cron/NAS.

---

## 🗕️ Running Periodically

If using Docker:

* Set `restart: always` and call script with cron logic inside the container
* Or use NAS scheduler / Portainer to run it every 15 minutes

If running on bare metal:

* Use `cron` or `Task Scheduler` to call `python main.py`

---

## 🧠 License

This project is licensed under the [GNU General Public License v3.0](https://github.com/Mouchoir/cloudflare-allow-my-ip/blob/main/LICENSE).
