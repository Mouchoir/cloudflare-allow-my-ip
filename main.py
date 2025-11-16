import os
import ipaddress
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_ACCESS_POLICY_ID = os.getenv("CF_ACCESS_POLICY_ID")

if not CF_API_TOKEN or not CF_ACCOUNT_ID or not CF_ACCESS_POLICY_ID:
    raise RuntimeError("Missing one of CF_API_TOKEN, CF_ACCOUNT_ID, CF_ACCESS_POLICY_ID in .env")

API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/access/policies/{CF_ACCESS_POLICY_ID}"

HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json",
}

# Public IP services (multiple providers for redundancy)
IPV4_SERVICES = [
    "https://ipv4.icanhazip.com/",
    "https://api.ipify.org",
    "https://v4.ident.me",
]

IPV6_SERVICES = [
    "https://ipv6.icanhazip.com/",
    "https://api64.ipify.org",
    "https://v6.ident.me",
]


def get_ip_from_services(services, family):
    """
    family = 4 or 6
    Try each service until one returns a valid IP of the requested family.
    """
    for url in services:
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            ip_str = resp.text.strip()
            ip_obj = ipaddress.ip_address(ip_str)

            if family == 4 and isinstance(ip_obj, ipaddress.IPv4Address):
                print(f"🌐 Using IPv4 {ip_str} from {url}")
                return ip_str

            if family == 6 and isinstance(ip_obj, ipaddress.IPv6Address):
                print(f"🌐 Using IPv6 {ip_str} from {url}")
                return ip_str

            print(f"⚠️ Ignoring {ip_str} from {url}: not IPv{family}")
        except Exception as e:
            print(f"❌ Error calling {url}: {e}")

    raise RuntimeError(f"Could not determine IPv{family} address from any service")


def get_current_ips():
    print("🔎 Getting current public IPv4...")
    ipv4 = get_ip_from_services(IPV4_SERVICES, 4)
    print(f"📍 Current IPv4: {ipv4}")
    print()  # blank line after IPv4 block

    ipv6 = None
    try:
        print("🔎 Getting current public IPv6...")
        ipv6 = get_ip_from_services(IPV6_SERVICES, 6)
        print(f"📍 Current IPv6: {ipv6}")
    except Exception as e:
        # IPv6 peut être absent ou mal routé, on n arrête pas tout pour ça
        print(f"⚠️ Warning: could not get IPv6 address: {e}")
        ipv6 = None

    print()  # blank line after IPv6 block (whether success or warning)
    return ipv4, ipv6


def ipv6_to_prefix(ipv6_str, prefix_length=64):
    """
    Transforme une IPv6 complète en préfixe /64 (ou autre longueur si besoin).
    Exemple: 2001:861:e3c4:f590:2054:d22b:da8:f4ae -> 2001:861:e3c4:f590::/64
    """
    ipv6_network = ipaddress.IPv6Network(f"{ipv6_str}/{prefix_length}", strict=False)
    return str(ipv6_network)


def get_policy():
    print("📦 Fetching Cloudflare Access policy...")
    response = requests.get(API_URL, headers=HEADERS)
    if response.status_code != 200:
        raise RuntimeError(f"❌ Failed to retrieve policy: {response.text}")
    return response.json()["result"]


def extract_current_ip_cidrs(policy_json):
    cidrs = []
    for rule in policy_json.get("include", []):
        if "ip" in rule and isinstance(rule["ip"], dict) and "ip" in rule["ip"]:
            cidrs.append(rule["ip"]["ip"])
    return cidrs


def build_desired_include(ipv4, ipv6_prefix):
    include = []

    if ipv4:
        include.append({"ip": {"ip": f"{ipv4}/32"}})

    if ipv6_prefix:
        include.append({"ip": {"ip": ipv6_prefix}})

    return include


def update_policy(policy_json, ipv4, ipv6_prefix):
    """
    Remplace le bloc include par:
      - IPv4 /32
      - IPv6 prefix (par ex. /64)
    Attention: ce script suppose que cette policy sert uniquement
    a whitelister tes IP (pas d autres types de regles dans include).
    """
    desired_include = build_desired_include(ipv4, ipv6_prefix)
    desired_cidrs = [rule["ip"]["ip"] for rule in desired_include]

    current_cidrs = extract_current_ip_cidrs(policy_json)

    if set(current_cidrs) == set(desired_cidrs):
        print(f"✅ IP ranges already up to date: {current_cidrs}")
        return

    print("🔄 Updating Cloudflare Access policy...")
    print(f"Old CIDRs: {current_cidrs}")
    print(f"New CIDRs: {desired_cidrs}")

    policy_json["include"] = desired_include

    update_response = requests.put(API_URL, headers=HEADERS, json=policy_json)
    if update_response.status_code != 200:
        raise RuntimeError(f"❌ Failed to update policy: {update_response.text}")

    print("✅ Policy successfully updated.")


def main():
    print("🚀 Starting Cloudflare IP updater...")
    print()  # blank line after start block

    ipv4, ipv6 = get_current_ips()

    if not ipv4:
        raise RuntimeError("❌ No public IPv4 found, aborting. Check your connectivity.")

    ipv6_prefix = None
    if ipv6:
        ipv6_prefix = ipv6_to_prefix(ipv6, 64)
        print(f"➡️ Using IPv6 prefix for policy: {ipv6_prefix}")
    else:
        print("ℹ️ No IPv6 prefix will be set in the policy (only IPv4).")

    print()  # blank line after IPv6 prefix / info block

    policy = get_policy()

    print("🛠️ Verifying and updating policy...")
    update_policy(policy, ipv4, ipv6_prefix)
    print("🏁 Done.")


if __name__ == "__main__":
    main()
