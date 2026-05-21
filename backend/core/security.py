"""
ScotlandAI Navigator — Download Token Security

Implements pre-signed, time-limited download URLs for generated PDFs
using itsdangerous — a lightweight signing library.

WHY THIS APPROACH:
- Briefs contain strategic organisational information — they should not be
  publicly accessible indefinitely
- 60-minute expiry balances usability (enough time to download) with security
- No database needed — the token itself contains the filename and timestamp,
  cryptographically signed with the server's secret key
- This keeps the backend completely stateless — a core architectural principle

HOW IT WORKS:
1. PDF is generated and saved with a UUID filename
2. generate_download_token() signs the filename with a timestamp
3. Token is returned as part of the brief response URL
4. When the user clicks the link, verify_download_token() checks:
   a. The signature is valid (not tampered with)
   b. The token is not older than PDF_EXPIRY_MINUTES
5. If valid, the PDF is served. If expired, HTTP 410 (Gone).
"""

from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from core.config import settings


# Singleton serializer — uses the server's SECRET_KEY
_serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

# Salt prevents tokens from one feature being reused in another
_SALT = "scotland-ai-navigator-pdf-download"


def generate_download_token(filename: str) -> str:
    """
    Create a signed, time-limited token for a PDF download.

    The token encodes the filename and the current timestamp.
    It can only be decoded with the same SECRET_KEY.
    """
    return _serializer.dumps(filename, salt=_SALT)


def verify_download_token(token: str) -> str:
    """
    Verify and decode a download token.

    Returns the original filename if valid.

    Raises:
        SignatureExpired: if the token is older than PDF_EXPIRY_MINUTES
        BadSignature: if the token has been tampered with
    """
    max_age_seconds = settings.PDF_EXPIRY_MINUTES * 60
    return _serializer.loads(token, salt=_SALT, max_age=max_age_seconds)
