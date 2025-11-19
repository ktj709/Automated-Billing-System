import http.client
import json

conn = http.client.HTTPSConnection("dev-t6knva248r1jkkvn.us.auth0.com")

payload = json.dumps({
    "client_id": "z06k7sgi5cuSBMQApQq8LKnGpwlkIUuA",
    "client_secret": "dTbuOjMvq36tuE8fZCm-O2rvzeel35qFvC1PdWqh2MfPTJNYM0cSsltAh3VU1MtL",
    "audience": "https://billing-api.example.com",
    "grant_type": "client_credentials"
})

headers = {'content-type': "application/json"}

conn.request("POST", "/oauth/token", payload, headers)

res = conn.getresponse()
data = res.read()

response_json = json.loads(data.decode("utf-8"))

if "access_token" in response_json:
    token = response_json["access_token"]
    print("\n" + "="*80)
    print("✅ JWT TOKEN RETRIEVED SUCCESSFULLY!")
    print("="*80)
    print(token)
    print("="*80)
    
    # Save to file
    with open('auth0_token.txt', 'w') as f:
        f.write(token)
    print("\n💾 Token saved to: auth0_token.txt")
    print("📋 Copy this token and paste it in the Streamlit 'JWT Token' field\n")
else:
    print("\n❌ Error getting token:")
    print(json.dumps(response_json, indent=2))
