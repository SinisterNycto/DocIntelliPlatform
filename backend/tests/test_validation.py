import pytest

from app.core.validation import safe_pdf_filename, validate_public_http_url


def test_public_urls_are_accepted():
    assert validate_public_http_url(" https://nodejs.org/api/cluster.html ") == "https://nodejs.org/api/cluster.html"


@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "http://localhost/admin",
    "http://127.0.0.1/secret",
    "http://169.254.169.254/latest/meta-data",
    "http://10.0.0.5/internal",
    "not a url",
])
def test_private_or_non_http_urls_are_rejected(url):
    with pytest.raises(ValueError):
        validate_public_http_url(url)


def test_pdf_filename_is_sanitized():
    assert safe_pdf_filename("../../weird name.pdf") == "weird_name.pdf"
    with pytest.raises(ValueError):
        safe_pdf_filename("notes.txt")
