"""Update check against GitHub Releases.

Why this exists: publishing a Release only notifies people who watch the repository. Someone
who merely downloaded the zip is invisible to GitHub, so the app has to ask GitHub itself.
That is exactly how "an update is available" notices reach users of most desktop apps.

Pure logic only (no Tk import): fetch + compare, so it can be unit-tested without a window.
The caller decides how to present the result.

Network policy:
  · a single short request, 8s timeout, offline or blocked -> silently gives up;
  · never raises, never blocks the UI (run it on a thread);
  · no user data is sent; the request carries only a User-Agent string.
"""

import json
import re
import urllib.error
import urllib.request

REPO = "yuannuo233/silver-wolf-desktop-pet"
API_LATEST = "https://api.github.com/repos/%s/releases/latest" % REPO
RELEASES_PAGE = "https://github.com/%s/releases/latest" % REPO
TIMEOUT = 8
USER_AGENT = "SilverWolfPet-UpdateCheck"

# Why a module-level flag: check() returns None for two very different outcomes — "already
# up to date" and "could not reach GitHub". The settings panel has to say which one happened,
# otherwise a blocked network looks like a clean bill of health.
last_error = None


def version_tuple(tag):
    """'v0.6.19' -> (0, 6, 19). Leading v and any non-numeric tail are ignored."""
    if not tag:
        return ()
    core = tag.strip().lstrip("vV")
    nums = re.findall(r"\d+", core)
    return tuple(int(n) for n in nums[:4])


def is_newer(latest_tag, current_tag):
    """True when latest_tag is a strictly higher version than current_tag.

    Compares numerically, not as strings: 'v0.6.10' is newer than 'v0.6.9', which a plain
    string comparison gets backwards. Missing components count as 0, so 'v0.7' > 'v0.6.99'.
    """
    a = version_tuple(latest_tag)
    b = version_tuple(current_tag)
    if not a or not b:
        return False
    width = max(len(a), len(b))
    a = a + (0,) * (width - len(a))
    b = b + (0,) * (width - len(b))
    return a > b


def _fetch_via_redirect(timeout=TIMEOUT):
    """Fallback with no API involved: /releases/latest redirects to /releases/tag/<tag>.

    This exists because the unauthenticated GitHub API allows only 60 requests per hour per
    IP. Everyone behind one NAT (a school, a dorm, a shared connection) shares that budget,
    and the check then silently fails with HTTP 403 — which is exactly what happened during
    testing here. The redirect carries the tag in its final URL and has no such quota.
    """
    req = urllib.request.Request(
        RELEASES_PAGE,
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            final = resp.geturl()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return None
    except Exception:
        return None
    m = re.search(r"/releases/tag/([^/?#]+)", final or "")
    if not m:
        return None
    return {"tag": m.group(1), "page": final, "notes": ""}


def fetch_latest(timeout=TIMEOUT):
    """Ask GitHub for the newest release.

    Returns a dict {tag, page, notes} or None. None means "no answer" — offline, blocked,
    rate-limited, private, or a malformed payload. Callers must treat it as "nothing to say",
    not as an error to show the user.

    Two channels on purpose: the API gives release notes but is capped at 60 requests/hour
    per IP; the plain redirect has no cap but no notes. The redirect is tried first so a
    shared IP cannot break the feature, and the API is the bonus that adds the changelog.
    """
    info = _fetch_via_redirect(timeout=timeout)
    if info:
        return info
    return _fetch_via_api(timeout=timeout)


def _fetch_via_api(timeout=TIMEOUT):
    req = urllib.request.Request(
        API_LATEST,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
        return None
    except Exception:
        return None

    if not isinstance(data, dict):
        return None
    tag = data.get("tag_name") or ""
    if not tag:
        return None
    return {
        "tag": tag,
        "page": data.get("html_url") or RELEASES_PAGE,
        "notes": (data.get("body") or "").strip(),
    }


def check(current_version, timeout=TIMEOUT):
    """One-shot check. Returns the release dict when an update exists, else None.

    Also sets `last_error`: None means GitHub answered (so None + no error = up to date),
    a string means the request failed. Without that distinction the UI cannot tell "you are
    current" from "I could not check".
    """
    global last_error
    last_error = None
    info = fetch_latest(timeout=timeout)
    if not info:
        last_error = "无法获取版本信息（网络不通、被限流或被拦截）"
        return None
    if is_newer(info["tag"], current_version):
        return info
    return None


def check_async(current_version, callback, timeout=TIMEOUT):
    """Run check() on a daemon thread; callback(result_or_None) runs on that thread.

    A daemon thread means a hung request can never keep the app alive after the user quits.
    """
    import threading

    def worker():
        try:
            result = check(current_version, timeout=timeout)
        except Exception:
            result = None
        try:
            callback(result)
        except Exception:
            pass

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return t
