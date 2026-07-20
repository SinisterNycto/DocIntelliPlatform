import os
import json
import jwt
import httpx
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.algorithms import RSAAlgorithm

security = HTTPBearer()

CLERK_ISSUER_URL = os.getenv("CLERK_ISSUER_URL") # e.g. "https://known-alien-12.clerk.accounts.dev"
CLERK_JWKS_URL = f"{CLERK_ISSUER_URL}/.well-known/jwks.json"

# Cache for the JWKS keys
_jwks_cache = None

async def get_jwks():
    global _jwks_cache
    if not _jwks_cache:
        async with httpx.AsyncClient() as client:
            response = await client.get(CLERK_JWKS_URL)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch Clerk JWKS")
            _jwks_cache = response.json()
    return _jwks_cache

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
    try:
        # Get unverified header to extract key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Invalid token header")
            
        jwks = await get_jwks()
        
        # Find the public key matching the kid
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key["kid"] == kid:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
                
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Public key not found in JWKS")
            
        public_key = RSAAlgorithm.from_jwk(json.dumps(rsa_key))
        
        # Verify the token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=CLERK_ISSUER_URL,
            options={"verify_aud": False}
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token payload missing sub (user_id)")
            
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")
