"""Offline site grouping using the bundled Public Suffix List (including private rules)."""
from functools import lru_cache
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlsplit


@lru_cache(maxsize=1)
def rules():
    exact, wild, exceptions = set(), set(), set()
    source = Path(__file__).parent / "data/public_suffix_list.dat"
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("//"):
            continue
        group, suffix = ((exceptions, line[1:]) if line.startswith("!") else
                         (wild, line[2:]) if line.startswith("*.") else (exact, line))
        group.add(suffix.encode("idna").decode("ascii").lower())
    return exact, wild, exceptions


@lru_cache(maxsize=32768)
def site(host):
    """Registrable domain; use the literal address/host if no registrable part exists."""
    host = host.lower().rstrip(".")
    try:
        return str(ip_address(host))
    except ValueError:
        pass
    try:
        labels = host.encode("idna").decode("ascii").split(".")
    except UnicodeError:
        return host
    exact, wild, exceptions = rules()
    size = 1
    for i in range(len(labels)):
        tail = ".".join(labels[i:])
        length = len(labels) - i
        if tail in exceptions:
            size = length - 1
            break
        if tail in exact:
            size = max(size, length)
        if i and tail in wild:
            size = max(size, length + 1)
    return ".".join(labels[-(size+1):])


def page_site(url):
    return site(urlsplit(url).hostname or "")
