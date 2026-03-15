# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import datetime
import logging
import re
import urllib.parse
from dataclasses import dataclass
from http.cookiejar import CookieJar

logger = logging.getLogger(__name__)

# Browsers to probe, in preference order.
_BROWSER_ORDER: list[tuple[str, str]] = [
    ("Chrome", "chrome"),
    ("Firefox", "firefox"),
    ("Edge", "edge"),
    ("Safari", "safari"),
    ("Opera", "opera"),
    ("Brave", "brave"),
    ("Vivaldi", "vivaldi"),
]

# Domains that indicate an active AOL session.
_AOL_DOMAINS: set[str] = {
    ".aol.com",
    ".login.aol.com",
    "login.aol.com",
    "mail.aol.com",
}

# Cookie names that signal an authenticated Yahoo/AOL session.
_SESSION_COOKIE_NAMES: set[str] = {"s", "d", "T", "Y"}

# Domains whose mere presence counts as a session indicator.
_LOGIN_DOMAINS: set[str] = {".login.aol.com", "login.aol.com", "mail.aol.com"}


@dataclass(frozen=True)
class AOLSession:
    """Detected AOL browser session."""

    username: str  # e.g., "user@aol.com"
    browser: str  # e.g., "Chrome", "Firefox"
    cookies: dict[str, str]  # cookie name -> value
    detected_at: datetime.datetime


def _is_aol_domain(domain: str) -> bool:
    """Return True if *domain* belongs to AOL's cookie scope."""
    domain_lower = domain.lower()
    if domain_lower in _AOL_DOMAINS:
        return True
    if domain_lower.endswith(".aol.com"):
        return True
    return False


def _extract_username_from_d_cookie(value: str) -> str | None:
    """Try to pull an email or user ID from Yahoo/AOL's ``d`` cookie.

    The ``d`` cookie is a long opaque blob, but historically contains
    URL-encoded fragments with ``login=<user>`` or ``u=<user>`` pairs.
    This is best-effort; the format is not documented.
    """
    try:
        decoded = urllib.parse.unquote(value)
    except Exception:
        return None

    # Look for login=<user@aol.com> or u=<user>
    for pattern in (
        r"login=([A-Za-z0-9_.+-]+@aol\.com)",
        r"\bu=([A-Za-z0-9_.+-]+@aol\.com)",
        r"login=([A-Za-z0-9_.+-]+)",
        r"\bu=([A-Za-z0-9_.+-]+)",
    ):
        match = re.search(pattern, decoded, re.IGNORECASE)
        if match:
            candidate = match.group(1)
            if "@" not in candidate:
                candidate = f"{candidate}@aol.com"
            return candidate
    return None


def _extract_username(cookies: dict[str, str]) -> str:
    """Derive the AOL username from session cookies, or fall back."""
    # 1. Try the ``d`` cookie (Yahoo/AOL session blob).
    d_val = cookies.get("d")
    if d_val:
        username = _extract_username_from_d_cookie(d_val)
        if username:
            return username

    # 2. Explicit login/user cookies.
    for key in ("login", "user", "userid", "username"):
        val = cookies.get(key)
        if val:
            if "@" not in val:
                return f"{val}@aol.com"
            return val

    return "AOL User"


def _get_cookiejar(browser_func_name: str) -> CookieJar | None:
    """Call the appropriate ``rookiepy`` loader, returning None on failure."""
    try:
        import rookiepy  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("rookiepy is not installed — cookie detection unavailable")
        return None

    loader = getattr(rookiepy, browser_func_name, None)
    if loader is None:
        logger.debug("rookiepy has no loader for %s", browser_func_name)
        return None

    try:
        return loader(domain_name=".aol.com")  # type: ignore[no-any-return]
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to load cookies via rookiepy.%s: %s", browser_func_name, exc)
        return None


def _aol_cookies_from_jar(jar: CookieJar) -> dict[str, str]:
    """Extract AOL-scoped cookies from a CookieJar."""
    result: dict[str, str] = {}
    for cookie in jar:
        domain = cookie.domain or ""
        if _is_aol_domain(domain):
            result[cookie.name] = cookie.value or ""
    return result


def _has_session_indicators(cookies: dict[str, str], jar: CookieJar) -> bool:
    """Return True if the cookies look like an active AOL session."""
    # Any known session cookie name present?
    if _SESSION_COOKIE_NAMES & set(cookies.keys()):
        return True

    # Any cookie from a login/mail subdomain?
    for cookie in jar:
        domain = (cookie.domain or "").lower()
        if domain in _LOGIN_DOMAINS:
            return True

    return False


def detect_aol_session() -> AOLSession | None:
    """Probe installed browsers for an active AOL Mail session.

    Returns the first successful ``AOLSession``, or ``None`` if no
    browser has recognisable AOL session cookies.  This function never
    raises; all errors are logged at DEBUG level.
    """
    try:
        import rookiepy  # type: ignore[import-untyped] # noqa: F401
    except ImportError:
        logger.debug("rookiepy is not installed — cookie detection unavailable")
        return None

    for display_name, func_name in _BROWSER_ORDER:
        logger.debug("Checking %s for AOL session cookies", display_name)
        jar = _get_cookiejar(func_name)
        if jar is None:
            continue

        cookies = _aol_cookies_from_jar(jar)
        if not cookies:
            logger.debug("%s: no AOL cookies found", display_name)
            continue

        if not _has_session_indicators(cookies, jar):
            logger.debug("%s: AOL cookies present but no session indicators", display_name)
            continue

        username = _extract_username(cookies)
        session = AOLSession(
            username=username,
            browser=display_name,
            cookies=cookies,
            detected_at=datetime.datetime.now(datetime.UTC),
        )
        logger.debug("Detected AOL session in %s for %s", display_name, username)
        return session

    logger.debug("No AOL session detected in any browser")
    return None


def list_detected_browsers() -> list[str]:
    """Return names of browsers where rookiepy can access cookies.

    Useful for telling the user which browsers were checked.
    Never raises; returns an empty list on failure.
    """
    accessible: list[str] = []

    try:
        import rookiepy  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("rookiepy is not installed — cannot list browsers")
        return accessible

    for display_name, func_name in _BROWSER_ORDER:
        loader = getattr(rookiepy, func_name, None)
        if loader is None:
            continue
        try:
            # A lightweight probe — just ask for cookies from a dummy domain
            # so we don't pull the entire jar.
            loader(domain_name=".example.invalid")
            accessible.append(display_name)
        except Exception:  # noqa: BLE001
            # Browser not installed, locked profile, missing keychain, etc.
            logger.debug("%s: not accessible", display_name)

    return accessible
