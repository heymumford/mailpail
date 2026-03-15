# Copyright (C) 2026+ Eric C. Mumford <eric@mumfordengineering.com>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Browser cookie extraction for email session detection.

Uses ``browser_cookie3`` to probe installed browsers for email
session cookies.  This is best-effort — all errors are swallowed
and logged at DEBUG level so the app never crashes from cookie issues.
"""

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
    ("Opera", "opera"),
    ("Brave", "brave"),
    ("Vivaldi", "vivaldi"),
    ("Safari", "safari"),
]

_AOL_DOMAINS: set[str] = {".aol.com", ".login.aol.com", "login.aol.com", "mail.aol.com"}
_SESSION_COOKIE_NAMES: set[str] = {"s", "d", "T", "Y"}
_LOGIN_DOMAINS: set[str] = {".login.aol.com", "login.aol.com", "mail.aol.com"}


@dataclass(frozen=True)
class BrowserSession:
    """Detected browser session."""

    username: str
    browser: str
    cookies: dict[str, str]
    detected_at: datetime.datetime


def _is_aol_domain(domain: str) -> bool:
    domain_lower = domain.lower()
    if domain_lower in _AOL_DOMAINS:
        return True
    return domain_lower.endswith(".aol.com")


def _extract_username_from_d_cookie(value: str) -> str | None:
    try:
        decoded = urllib.parse.unquote(value)
    except Exception:
        return None

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
    d_val = cookies.get("d")
    if d_val:
        username = _extract_username_from_d_cookie(d_val)
        if username:
            return username
    for key in ("login", "user", "userid", "username"):
        val = cookies.get(key)
        if val:
            return f"{val}@aol.com" if "@" not in val else val
    return "AOL User"


def _get_cookiejar(browser_func_name: str) -> CookieJar | None:
    try:
        import browser_cookie3  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("browser_cookie3 is not installed — cookie detection unavailable")
        return None

    loader = getattr(browser_cookie3, browser_func_name, None)
    if loader is None:
        logger.debug("browser_cookie3 has no loader for %s", browser_func_name)
        return None

    try:
        return loader(domain_name=".aol.com")  # type: ignore[no-any-return]
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to load cookies via browser_cookie3.%s: %s", browser_func_name, exc)
        return None


def _aol_cookies_from_jar(jar: CookieJar) -> dict[str, str]:
    result: dict[str, str] = {}
    for cookie in jar:
        domain = cookie.domain or ""
        if _is_aol_domain(domain):
            result[cookie.name] = cookie.value or ""
    return result


def _has_session_indicators(cookies: dict[str, str], jar: CookieJar) -> bool:
    if _SESSION_COOKIE_NAMES & set(cookies.keys()):
        return True
    for cookie in jar:
        domain = (cookie.domain or "").lower()
        if domain in _LOGIN_DOMAINS:
            return True
    return False


def detect_browser_session() -> BrowserSession | None:
    """Probe installed browsers for an active email session.

    Returns the first successful ``BrowserSession``, or ``None``.
    Never raises.
    """
    try:
        import browser_cookie3  # type: ignore[import-untyped]  # noqa: F401
    except ImportError:
        logger.debug("browser_cookie3 is not installed — cookie detection unavailable")
        return None

    for display_name, func_name in _BROWSER_ORDER:
        logger.debug("Checking %s for session cookies", display_name)
        jar = _get_cookiejar(func_name)
        if jar is None:
            continue

        cookies = _aol_cookies_from_jar(jar)
        if not cookies:
            logger.debug("%s: no cookies found", display_name)
            continue

        if not _has_session_indicators(cookies, jar):
            logger.debug("%s: cookies present but no session indicators", display_name)
            continue

        username = _extract_username(cookies)
        session = BrowserSession(
            username=username,
            browser=display_name,
            cookies=cookies,
            detected_at=datetime.datetime.now(datetime.UTC),
        )
        logger.debug("Detected session in %s for %s", display_name, username)
        return session

    logger.debug("No session detected in any browser")
    return None


def list_detected_browsers() -> list[str]:
    """Return names of browsers where cookie access works. Never raises."""
    accessible: list[str] = []
    try:
        import browser_cookie3  # type: ignore[import-untyped]
    except ImportError:
        return accessible

    for display_name, func_name in _BROWSER_ORDER:
        loader = getattr(browser_cookie3, func_name, None)
        if loader is None:
            continue
        try:
            loader(domain_name=".example.invalid")
            accessible.append(display_name)
        except Exception:  # noqa: BLE001
            logger.debug("%s: not accessible", display_name)

    return accessible
