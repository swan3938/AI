import os
import time
import jwt

def create_access_token(user_id: str, role: str) -> str:
    payload = {"sub": user_id, "role": role, "iat": int(time.time()), "exp": int(time.time()) + 3600}
    secret = os.getenv("JWT_SECRET", "change_me")
    return jwt.encode(payload, secret, algorithm="HS256")

def decode_token(token: str) -> dict:
    secret = os.getenv("JWT_SECRET", "change_me")
    return jwt.decode(token, secret, algorithms=["HS256"])
