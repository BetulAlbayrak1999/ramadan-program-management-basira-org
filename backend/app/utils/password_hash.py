"""
Lightweight password hashing using stdlib pbkdf2_hmac.
Drop-in replacement for passlib/bcrypt with same API.
Provides secure password hashing using PBKDF2-HMAC-SHA256.
"""
import hashlib
import hmac
import os
import base64


# Number of iterations for PBKDF2 (100,000 is OWASP recommendation for SHA256)
ITERATIONS = 100000


class _BcryptHashCompat:
    """
    Compatibility class that mimics passlib.hash.bcrypt API.
    Uses PBKDF2-HMAC-SHA256 instead of bcrypt for lighter bundle.
    """
    
    @staticmethod
    def hash(password: str) -> str:
        """
        Hash a password using PBKDF2-HMAC-SHA256.
        
        Args:
            password: Plain text password
            
        Returns:
            Hash string in format: pbkdf2_sha256$iterations$salt$hash
        """
        # Generate random salt (32 bytes = 256 bits)
        salt = os.urandom(32)
        
        # Hash password
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            ITERATIONS
        )
        
        # Encode salt and key as base64 for storage
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        key_b64 = base64.b64encode(key).decode('utf-8')
        
        # Return in a format similar to Django/passlib
        return f"pbkdf2_sha256${ITERATIONS}${salt_b64}${key_b64}"
    
    @staticmethod
    def verify(password: str, hash_string: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            password: Plain text password to verify
            hash_string: Hash string from hash() method
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            # Parse hash string
            parts = hash_string.split('$')
            
            # Handle both new format (pbkdf2) and legacy bcrypt hashes
            if len(parts) == 4 and parts[0] == 'pbkdf2_sha256':
                # New pbkdf2 format
                iterations = int(parts[1])
                salt = base64.b64decode(parts[2])
                stored_key = base64.b64decode(parts[3])
                
                # Hash the provided password with same salt
                key = hashlib.pbkdf2_hmac(
                    'sha256',
                    password.encode('utf-8'),
                    salt,
                    iterations
                )
                
                # Compare using constant-time comparison
                return hmac.compare_digest(key, stored_key)
            
            else:
                # Legacy bcrypt format - need actual bcrypt
                # This handles backward compatibility if you have existing bcrypt hashes
                try:
                    import bcrypt
                    return bcrypt.checkpw(
                        password.encode('utf-8'),
                        hash_string.encode('utf-8')
                    )
                except ImportError:
                    # If bcrypt not available and hash is in bcrypt format, fail
                    raise ValueError(
                        "Legacy bcrypt hash detected but bcrypt not installed. "
                        "Please reset password or install bcrypt for migration."
                    )
        
        except Exception as e:
            # Log the error in production
            print(f"Password verification error: {e}")
            return False


# Export as bcrypt_hash to match original import
bcrypt_hash = _BcryptHashCompat()


# Also provide a passlib-style interface
class hash:
    """Namespace class to match passlib.hash structure"""
    bcrypt = bcrypt_hash
