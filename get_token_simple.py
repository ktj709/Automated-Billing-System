import json
import os

import requests


def _get_env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def main() -> int:
    """Fetch an Auth0 access token using Client Credentials flow.

    Required env vars:
      - AUTH0_DOMAIN
      - AUTH0_API_IDENTIFIER (audience)
      - AUTH0_M2M_CLIENT_ID
      - AUTH0_M2M_CLIENT_SECRET

    Optional:
      - AUTH0_TOKEN_SAVE_FILE=auth0_token.txt (default)
      - AUTH0_TOKEN_SAVE=1 to write token to file (default: 1)
    """

    auth0_domain = _get_env("AUTH0_DOMAIN")
    audience = _get_env("AUTH0_API_IDENTIFIER")
    client_id = _get_env("AUTH0_M2M_CLIENT_ID")
    client_secret = _get_env("AUTH0_M2M_CLIENT_SECRET")

    if not auth0_domain or not audience or not client_id or not client_secret:
        print("❌ Missing Auth0 configuration.")
        print("Set: AUTH0_DOMAIN, AUTH0_API_IDENTIFIER, AUTH0_M2M_CLIENT_ID, AUTH0_M2M_CLIENT_SECRET")
        return 1

    url = f"https://{auth0_domain}/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
        "grant_type": "client_credentials",
    }

    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"\n❌ Error getting token: {e}")
        try:
            print(resp.text[:1000])
        except Exception:
            pass
        return 1

    token = data.get("access_token")
    if not token:
        print("\n❌ No access_token returned:")
        print(json.dumps(data, indent=2)[:2000])
        return 1

    print("\n" + "=" * 80)
    print("✅ JWT TOKEN RETRIEVED SUCCESSFULLY!")
    print("=" * 80)
    print(token)
    print("=" * 80)

    save_enabled = _get_env("AUTH0_TOKEN_SAVE")
    if save_enabled == "":
        save_enabled = "1"

    if save_enabled not in {"0", "false", "False", "no", "NO"}:
        out_path = _get_env("AUTH0_TOKEN_SAVE_FILE") or "auth0_token.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(token)
        print(f"\n💾 Token saved to: {out_path}")

    print("📋 Copy this token and paste it in the Streamlit 'JWT Token' field\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
