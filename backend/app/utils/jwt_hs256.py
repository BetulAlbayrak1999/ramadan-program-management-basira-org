"""
Lightweight JWT HS256 implementation using only Python stdlib.
Drop-in replacement for python-jose for HS256 tokens.
"""
import hmac
import hashlib
import json
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class JWTError(Exception):
    """JWT validation error"""
    pass


def _base64url_encode(data: bytes) -> str:
    """Base64 URL-safe encoding without padding"""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _base64url_decode(data: str) -> bytes:
    """Base64 URL-safe decoding with padding"""
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def encode(payload: Dict[str, Any], key: str, algorithm: str = "HS256") -> str:
    """
    Create a JWT token.
    
    Args:
        payload: Dictionary with claims
        key: Secret key for signing
        algorithm: Only "HS256" is supported
        
    Returns:
        JWT token string
    """
    if algorithm != "HS256":
        raise ValueError(f"Algorithm {algorithm} not supported. Only HS256 is supported.")
    
    # Header
    header = {
        "typ": "JWT",
        "alg": "HS256"
    }
    
    # Encode header and payload
    header_b64 = _base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    # Create signature
    message = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(
        key.encode('utf-8'),
        message,
        hashlib.sha256
    ).digest()
    signature_b64 = _base64url_encode(signature)
    
    # Return complete token
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode(token: str, key: str, algorithms: list = None) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string
        key: Secret key for verification
        algorithms: List of allowed algorithms (only HS256 supported)
        
    Returns:
        Decoded payload dictionary
        
    Raises:
        JWTError: If token is invalid, expired, or signature doesn't match
    """
    if algorithms and "HS256" not in algorithms:
        raise JWTError("Only HS256 algorithm is supported")
    
    try:
        # Split token
        parts = token.split('.')
        if len(parts) != 3:
            raise JWTError("Invalid token format")
        
        header_b64, payload_b64, signature_b64 = parts
        
        # Verify signature
        message = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_signature = hmac.new(
            key.encode('utf-8'),
            message,
            hashlib.sha256
        ).digest()
        
        provided_signature = _base64url_decode(signature_b64)
        
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise JWTError("Signature verification failed")
        
        # Decode payload
        payload_json = _base64url_decode(payload_b64)
        payload = json.loads(payload_json)
        
        # Check expiration
        if 'exp' in payload:
            exp = payload['exp']
            now = datetime.now(timezone.utc).timestamp()
            if now >= exp:
                raise JWTError("Token has expired")
        
        return payload
        
    except JWTError:
        raise
    except Exception as e:
        raise JWTError(f"Invalid token: {str(e)}")


# Alias for compatibility
class jwt:
    """Compatibility class to match python-jose API"""
    encode = staticmethod(encode)
    decode = staticmethod(decode)
