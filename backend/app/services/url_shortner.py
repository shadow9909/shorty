"""URL shortening service with base62 encoding."""
import string
import secrets
from typing import Optional
from app.config import settings

# Base62 alphabet (a-z, A-Z, 0-9)
BASE62_ALPHABET = string.ascii_lowercase + string.ascii_uppercase + string.digits


def encode_base62(num: int) -> str:
    """Encode a number to base62 string.
    
    Args:
        num: Integer to encode
        
    Returns:
        Base62 encoded string
    """
    if num == 0:
        return BASE62_ALPHABET[0]
    
    result = []
    while num > 0:
        num, remainder = divmod(num, 62)
        result.append(BASE62_ALPHABET[remainder])
    
    return ''.join(reversed(result))


def decode_base62(encoded: str) -> int:
    """Decode a base62 string to number.
    
    Args:
        encoded: Base62 encoded string
        
    Returns:
        Decoded integer
    """
    num = 0
    for char in encoded:
        num = num * 62 + BASE62_ALPHABET.index(char)
    return num


def generate_short_code(length: Optional[int] = None) -> str:
    """Generate a random short code.
    
    Uses cryptographically secure random generation.
    
    Args:
        length: Length of short code (defaults to settings.short_code_length)
        
    Returns:
        Random short code string
    """
    if length is None:
        length = settings.short_code_length
    
    return ''.join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


def is_valid_short_code(short_code: str) -> bool:
    """Validate a short code format.
    
    Args:
        short_code: Short code to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not short_code:
        return False
    
    # Check length (between 3 and 10 characters)
    if not (3 <= len(short_code) <= 10):
        return False
    
    # Check if all characters are in base62 alphabet
    return all(char in BASE62_ALPHABET for char in short_code)


def generate_unique_short_code(
    existing_codes: set[str],
    custom_alias: Optional[str] = None,
    max_attempts: int = 10
) -> Optional[str]:
    """Generate a unique short code, avoiding collisions.
    
    Args:
        existing_codes: Set of existing short codes to avoid
        custom_alias: Optional custom alias to use
        max_attempts: Maximum number of generation attempts
        
    Returns:
        Unique short code if successful, None if max attempts exceeded
    """
    # If custom alias provided, validate and use it
    if custom_alias:
        if not is_valid_short_code(custom_alias):
            raise ValueError("Invalid custom alias format")
        if custom_alias in existing_codes:
            raise ValueError("Custom alias already exists")
        return custom_alias
    
    # Generate random short code
    for _ in range(max_attempts):
        short_code = generate_short_code()
        if short_code not in existing_codes:
            return short_code
    
    # If we couldn't generate a unique code, try with longer length
    for _ in range(max_attempts):
        short_code = generate_short_code(length=settings.short_code_length + 1)
        if short_code not in existing_codes:
            return short_code
    
    return None