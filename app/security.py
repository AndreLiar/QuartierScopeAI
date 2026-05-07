import re
from ipaddress import ip_address
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator
from secure import Secure
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

QUERY_CHARSET = re.compile(
    r"^["
    r"a-zA-Z0-9_\s"
    r"À-ÿ"
    r".,;:!?'\"\-/€%()\[\]+&@#*=<>"
    r"—–…«»‘’“”"
    r"]*$"
)
MAX_QUERY_LEN = 2000


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=MAX_QUERY_LEN)
    deal_id: str | None = Field(default=None, max_length=64)
    confirm: bool = False
    history: list[dict[str, str]] = Field(default_factory=list, max_length=20)

    @field_validator("query")
    @classmethod
    def safe_charset(cls, v: str) -> str:
        if not QUERY_CHARSET.match(v):
            raise ValueError("query contains disallowed characters")
        return v.strip()


def is_private_or_loopback(host: str) -> bool:
    try:
        ip = ip_address(host)
    except ValueError:
        return False
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def assert_url_is_public(url: str) -> None:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if is_private_or_loopback(host):
        raise ValueError(f"refused private/loopback URL: {url}")


secure_headers = Secure.with_default_headers()
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)
