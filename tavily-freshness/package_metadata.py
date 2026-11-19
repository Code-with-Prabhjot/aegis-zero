"""
AEGIS-0 Package Metadata Grounding (PyPI)

Grounds the freshness formula's inputs in real release data instead of
constants, using PyPI's free JSON API (no Tavily credits spent):

- release dates for any version of a package,
- the latest version and its release date,
- version pins read from requirements*.txt / pyproject.toml.

Network failures never break verification: lookups time out quickly, results
(including failures) are cached, and AEGIS_PYPI_OFFLINE=1 disables the
network entirely.
"""

import os
import re
import time
from datetime import datetime, timezone
from typing import Callable, Dict, Optional, Tuple

import httpx

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

# Import name -> PyPI distribution name, where they differ.
IMPORT_TO_DISTRIBUTION: Dict[str, str] = {
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "PIL": "Pillow",
    "cv2": "opencv-python",
    "bs4": "beautifulsoup4",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "jwt": "PyJWT",
    "google": "google-api-python-client",
    "langchain_openai": "langchain-openai",
    "langchain_community": "langchain-community",
}

_REQ_LINE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(==|~=|>=)\s*([0-9][0-9A-Za-z.\-+]*)")


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def distribution_for(import_root: str) -> str:
    return IMPORT_TO_DISTRIBUTION.get(import_root, import_root)


def major_version(version: Optional[str]) -> Optional[int]:
    if not version:
        return None
    m = re.match(r"(\d+)", version)
    return int(m.group(1)) if m else None


def parse_dependency_pins(repo_dir: Optional[str]) -> Dict[str, str]:
    """
    Reads version pins (==, ~=, >=) from requirements*.txt and pyproject.toml
    at the top of `repo_dir` (or its first-level subdirectories). Keys are
    normalized distribution names.
    """
    pins: Dict[str, str] = {}
    if not repo_dir or not os.path.isdir(repo_dir):
        return pins

    candidates = [repo_dir] + [
        os.path.join(repo_dir, d) for d in sorted(os.listdir(repo_dir))
        if os.path.isdir(os.path.join(repo_dir, d)) and not d.startswith(".")
    ]
    for directory in candidates:
        for fname in sorted(os.listdir(directory)):
            path = os.path.join(directory, fname)
            if fname.startswith("requirements") and fname.endswith(".txt"):
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        m = _REQ_LINE.match(line.split("#", 1)[0])
                        if m:
                            pins.setdefault(normalize(m.group(1)), m.group(3))
            elif fname == "pyproject.toml" and tomllib is not None:
                try:
                    with open(path, "rb") as fh:
                        data = tomllib.load(fh)
                except Exception:
                    continue
                for dep in data.get("project", {}).get("dependencies", []) or []:
                    m = _REQ_LINE.match(dep)
                    if m:
                        pins.setdefault(normalize(m.group(1)), m.group(3))
    return pins


def _parse_time(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


class PyPIMetadata:
    """Cached PyPI JSON API client."""

    ENDPOINT = "https://pypi.org/pypi/{name}/json"
    CACHE_TTL_SECONDS = 24 * 3600
    FAILURE_TTL_SECONDS = 600

    def __init__(
        self,
        offline: Optional[bool] = None,
        timeout: float = 3.0,
        fetcher: Optional[Callable[[str], Optional[dict]]] = None,
    ):
        if offline is None:
            offline = os.getenv("AEGIS_PYPI_OFFLINE", "").lower() in ("1", "true", "yes")
        self.offline = offline
        self.timeout = timeout
        self._fetcher = fetcher or self._http_fetch
        self._cache: Dict[str, Tuple[float, Optional[dict]]] = {}
        self.requests_made = 0

    def _http_fetch(self, name: str) -> Optional[dict]:
        with httpx.Client(timeout=self.timeout) as client:
            res = client.get(self.ENDPOINT.format(name=name))
            if res.status_code == 404:
                return None
            res.raise_for_status()
            return res.json()

    def package(self, name: str) -> Optional[dict]:
        """
        Returns {"name", "latest_version", "latest_release": datetime,
        "release_dates": {version: datetime}} or None if unavailable.
        """
        key = normalize(name)
        cached = self._cache.get(key)
        now = time.time()
        if cached:
            ttl = self.CACHE_TTL_SECONDS if cached[1] is not None else self.FAILURE_TTL_SECONDS
            if now - cached[0] < ttl:
                return cached[1]
        if self.offline and self._fetcher == self._http_fetch:
            return None

        info: Optional[dict] = None
        try:
            self.requests_made += 1
            raw = self._fetcher(name)
            if raw:
                release_dates: Dict[str, datetime] = {}
                for version, files in (raw.get("releases") or {}).items():
                    times = [t for t in (_parse_time(f.get("upload_time_iso_8601", "")) for f in files) if t]
                    if times:
                        release_dates[version] = min(times)
                latest = (raw.get("info") or {}).get("version")
                info = {
                    "name": (raw.get("info") or {}).get("name", name),
                    "latest_version": latest,
                    "latest_release": release_dates.get(latest),
                    "release_dates": release_dates,
                }
        except Exception:
            info = None
        self._cache[key] = (now, info)
        return info

    @staticmethod
    def days_between(earlier: Optional[datetime], later: Optional[datetime] = None) -> Optional[float]:
        if earlier is None:
            return None
        later = later or datetime.now(timezone.utc)
        return max(0.0, (later - earlier).total_seconds() / 86400.0)
