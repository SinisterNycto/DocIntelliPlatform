import ipaddress
import os
import re
from urllib.parse import urlparse


def validate_public_http_url(url: str) -> str:
    """Accept only public http(s) URLs. Rejects loopback, link-local, and private hosts."""
    cleaned = (url or "").strip()
    parsed = urlparse(cleaned)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not host:
        raise ValueError("Only public http(s) URLs are supported")
    if host in {"localhost", "metadata.google.internal"} or host.endswith(".local"):
        raise ValueError("That URL is not allowed")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip and (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast):
        raise ValueError("That URL is not allowed")
    return cleaned


def safe_pdf_filename(filename: str) -> str:
    base = os.path.basename(filename or "")
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base).strip("._")
    if not cleaned.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported")
    return cleaned[:180]
