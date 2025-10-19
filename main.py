import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_ACCESS_POLICY_ID = os.getenv("CF_ACCESS_POLICY_ID")

API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/access/policies/{CF_ACCESS_POLICY_ID}"

HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json"
}

def get_current_ip():
    try:
        ip = requests.get("https://ipv4.icanhazip.com/", timeout=5).text.strip()
        return ip
    except Exception as e:
        raise RuntimeError(f"Failed to get public IP: {e}")

def get_policy():
    response = requests.get(API_URL, headers=HEADERS)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to retrieve policy: {response.text}")
    return response.json()["result"]

def update_policy(policy_json, new_ip):
    current_include = policy_json.get("include", [])
    current_ip = None

    for rule in current_include:
        if "ip" in rule and isinstance(rule["ip"], dict):
            current_ip = rule["ip"].get("ip")

    if current_ip == f"{new_ip}/32":
        print(f"✅ IP is already up to date: {current_ip}")
        return

    print(f"🔄 Updating IP from {current_ip} to {new_ip}/32")
    policy_json["include"] = [
        { "ip": { "ip": f"{new_ip}/32" } }
    ]

    update_response = requests.put(API_URL, headers=HEADERS, json=policy_json)
    if update_response.status_code != 200:
        raise RuntimeError(f"❌ Failed to update policy: {update_response.text}")

    print("✅ Policy successfully updated.")

def main():
    print("🌐 Getting current public IP...")
    current_ip = get_current_ip()
    print(f"📍 Current IP: {current_ip}")

    print("📦 Fetching Cloudflare Access policy...")
    policy = get_policy()

    print("🛠️ Verifying and updating policy...")
    update_policy(policy, current_ip)

if __name__ == "__main__":
    main()