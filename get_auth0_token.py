"""
Script to get Auth0 JWT token for testing
"""
import requests
import json
from config import Config

def get_auth0_token():
    """Get JWT token from Auth0"""
    
    # Check if Auth0 is configured
    if not Config.AUTH0_DOMAIN or not Config.AUTH0_API_IDENTIFIER:
        print("❌ Auth0 not configured in .env")
        print("Please set AUTH0_DOMAIN and AUTH0_API_IDENTIFIER")
        return
    
    print(f"🔐 Getting Auth0 token...")
    print(f"Domain: {Config.AUTH0_DOMAIN}")
    print(f"API Identifier: {Config.AUTH0_API_IDENTIFIER}")
    print()
    
    # You need to configure these in your .env file
    client_id = input("Enter your Auth0 Client ID: ").strip()
    client_secret = input("Enter your Auth0 Client Secret: ").strip()
    
    # Token endpoint
    url = f"https://{Config.AUTH0_DOMAIN}/oauth/token"
    
    # Request payload for client credentials flow
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": Config.AUTH0_API_IDENTIFIER,
        "grant_type": "client_credentials"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        token = data.get('access_token')
        
        print("\n✅ Token retrieved successfully!")
        print("\n" + "="*80)
        print("JWT TOKEN:")
        print("="*80)
        print(token)
        print("="*80)
        print("\n📋 Copy this token and paste it in the Streamlit 'JWT Token' field")
        
        # Save to file for convenience
        with open('auth0_token.txt', 'w') as f:
            f.write(token)
        print("💾 Token also saved to: auth0_token.txt")
        
        return token
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error getting token: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None


def get_token_with_username_password():
    """Get token using username/password (Resource Owner Password flow)"""
    
    if not Config.AUTH0_DOMAIN or not Config.AUTH0_API_IDENTIFIER:
        print("❌ Auth0 not configured in .env")
        return
    
    print("🔐 Getting Auth0 token with username/password...")
    print()
    
    client_id = input("Enter your Auth0 Client ID: ").strip()
    username = input("Enter username/email: ").strip()
    password = input("Enter password: ").strip()
    
    url = f"https://{Config.AUTH0_DOMAIN}/oauth/token"
    
    payload = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "audience": Config.AUTH0_API_IDENTIFIER,
        "client_id": client_id,
        "scope": "openid profile email"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        token = data.get('access_token')
        
        print("\n✅ Token retrieved successfully!")
        print("\n" + "="*80)
        print("JWT TOKEN:")
        print("="*80)
        print(token)
        print("="*80)
        
        with open('auth0_token.txt', 'w') as f:
            f.write(token)
        print("\n💾 Token saved to: auth0_token.txt")
        
        return token
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


if __name__ == "__main__":
    print("Auth0 Token Generator")
    print("=" * 80)
    print()
    print("Choose authentication method:")
    print("1. Client Credentials (M2M - Machine to Machine)")
    print("2. Username/Password (Resource Owner)")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        get_auth0_token()
    elif choice == "2":
        get_token_with_username_password()
    else:
        print("Invalid choice")
