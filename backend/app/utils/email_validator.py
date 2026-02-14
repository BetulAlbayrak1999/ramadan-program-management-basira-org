"""
Lightweight email validation without extra dependencies.
Simple replacement for pydantic EmailStr.
"""
import re


# Simple but effective email regex pattern (RFC 5322 simplified)
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)


def validate_email(email: str) -> str:
    """
    Validate email format using regex.
    
    Args:
        email: Email string to validate
        
    Returns:
        Lowercase email string
        
    Raises:
        ValueError: If email format is invalid
    """
    if not email or not isinstance(email, str):
        raise ValueError("Email must be a non-empty string")
    
    email = email.strip().lower()
    
    if not EMAIL_PATTERN.match(email):
        raise ValueError("Invalid email format")
    
    return email
