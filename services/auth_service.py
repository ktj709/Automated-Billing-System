import requests
from typing import Dict, Optional
from config import Config

# Import jose only if available (optional for Auth0)
try:
    from jose import jwt
    HAS_JOSE = True
except ImportError:
    HAS_JOSE = False


class AuthService:
    """Authentication service for validating Auth0 tokens"""
    
    def __init__(self):
        self.domain = Config.AUTH0_DOMAIN
        self.api_identifier = Config.AUTH0_API_IDENTIFIER
        self.algorithms = ["RS256"]
        self.auth0_enabled = HAS_JOSE and self.domain and self.api_identifier
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify Auth0 JWT token
        
        Args:
            token: JWT token from request header
        
        Returns:
            Dict with user info if valid, None if invalid
        """
        
        if not self.auth0_enabled:
            return None
        
        try:
            # Get Auth0 public key
            jwks_url = f"https://{self.domain}/.well-known/jwks.json"
            jwks_response = requests.get(jwks_url, timeout=10)
            jwks = jwks_response.json()
            
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            
            # Find the right key
            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
                    break
            
            if not rsa_key:
                return None
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=self.algorithms,
                audience=self.api_identifier,
                issuer=f"https://{self.domain}/"
            )
            
            return payload
        
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTClaimsError:
            return None
        except Exception:
            return None
    
    def verify_header_auth(self, token: str) -> bool:
        """
        Verify simple header authentication token
        
        Args:
            token: Token from request header
        
        Returns:
            True if valid, False otherwise
        """
        return token == Config.HEADER_AUTH_TOKEN
