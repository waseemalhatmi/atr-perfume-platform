import re
import unicodedata


def generate_slug(text: str) -> str:
    """
    Convert arbitrary text (including Arabic) into a URL-safe slug.

    Steps:
        1. Normalize Unicode (NFKD) so accented chars are decomposed.
        2. Encode to ASCII bytes, ignoring non-ASCII (removes diacritics).
        3. Decode back to string.
        4. Lower-case.
        5. Replace any run of spaces / hyphens with a single '-'.
        6. Strip leading / trailing hyphens.

    For Arabic names where all chars are stripped, falls back to the
    raw lower-cased, space-replaced version so slugs are never empty.
    """
    if not text:
        return ''

    # Try ASCII-safe path first (works well for Latin text)
    normalized = unicodedata.normalize('NFKD', text)
    ascii_slug = normalized.encode('ascii', 'ignore').decode('ascii')
    ascii_slug = ascii_slug.lower()
    ascii_slug = re.sub(r'[\s\-]+', '-', ascii_slug).strip('-')

    if ascii_slug:
        return ascii_slug

    # Fallback for fully non-ASCII text (e.g., pure Arabic names):
    # keep original chars, just normalise whitespace → hyphens
    fallback = text.strip().lower()
    fallback = re.sub(r'[\s\-]+', '-', fallback).strip('-')
    return fallback
