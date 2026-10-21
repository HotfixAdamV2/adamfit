"""Talk to the Google Health API (where Fitbit data lives) and sync weigh-ins.

The flow, in short:

1. ``build_auth_url`` makes a Google login link. A random ``state`` value is
   stored in the database so the redirect back can be matched to the user.
2. Google redirects to ``http://localhost:8501/?code=...&state=...``.
   That opens a new, logged-out Streamlit session, so ``app.py`` passes the
   query parameters to ``handle_callback``, which finds the user by state
   and stores their tokens. It never logs anyone in.
3. ``sync_weights`` gets a fresh access token, downloads the weigh-ins for a
   date range, keeps the latest one per day and saves them.

Setup steps are in ``docs/google_health_setup.md``. Tokens and the client
secret are never printed, logged or put in error messages.
"""

import os
import secrets
from datetime import UTC, date, datetime, timedelta
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

from adamfit import google_health_connection, weights

load_dotenv()

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
API_URL = "https://health.googleapis.com/v4/users/me"

WEIGHT_SCOPE = "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly"
# All four are asked for now, so later syncs (nutrition, sleep, activity)
# won't need the user to approve again
SCOPES = [
    "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly",
    WEIGHT_SCOPE,
    "https://www.googleapis.com/auth/googlehealth.nutrition.readonly",
    "https://www.googleapis.com/auth/googlehealth.sleep.readonly",
]

REQUEST_TIMEOUT_SECONDS = 30
STATE_LIFETIME = timedelta(minutes=10)
# Refresh the access token this long before it really expires, so it can't
# run out in the middle of a sync
TOKEN_EXPIRY_MARGIN = timedelta(seconds=60)
PAGE_SIZE = 10000

RECONNECT_HINT = "Click **Connect Google Health** on the My Profile page, Weight tab, to connect again."


class GoogleHealthError(Exception):
    """
    Base class for Google Health problems. The message is written for the user.
    """


class NotConfiguredError(GoogleHealthError):
    """
    Raised when the GOOGLE_HEALTH_* settings are missing from ``.env``.
    """


class NotConnectedError(GoogleHealthError):
    """
    Raised when the user has no working connection and must (re)connect.
    """


class ApiError(GoogleHealthError):
    """
    Raised when Google can't be reached or returns an error.
    """


# ---- Settings ----------------------------------------------------------
def get_config() -> dict | None:
    """
    Read the Google Health settings from the environment (the root ``.env``).

    Returns
    -------
    dict | None
        ``client_id``, ``client_secret`` and ``redirect_uri``, or None if
        any of them is missing.
    """
    config = {
        "client_id": os.environ.get("GOOGLE_HEALTH_CLIENT_ID", "").strip(),
        "client_secret": os.environ.get("GOOGLE_HEALTH_CLIENT_SECRET", "").strip(),
        "redirect_uri": os.environ.get("GOOGLE_HEALTH_REDIRECT_URI", "").strip(),
    }
    if not all(config.values()):
        return None
    return config


def is_configured() -> bool:
    """
    Check whether the Google Health settings are present.

    Returns
    -------
    bool
        True if ``get_config`` finds all three settings.
    """
    return get_config() is not None


def _require_config() -> dict:
    """
    Return the settings, or raise if they are missing.

    Returns
    -------
    dict
        See ``get_config``.

    Raises
    ------
    NotConfiguredError
        If any setting is missing.
    """
    config = get_config()
    if config is None:
        raise NotConfiguredError(
            "Google Health isn't set up yet. Add the GOOGLE_HEALTH_* settings to `.env` "
            "(see `docs/google_health_setup.md`) and restart the app."
        )
    return config


# ---- Small HTTP helpers ------------------------------------------------
def _google_error(response: requests.Response) -> str:
    """
    Pull Google's own error message out of a failed response.

    Token endpoints answer ``{"error": "...", "error_description": "..."}``,
    and the Health API answers ``{"error": {"message": "...", ...}}``.

    Parameters
    ----------
    response : requests.Response
        A response with an error status.

    Returns
    -------
    str
        A short description such as ``"HTTP 403: The caller does not have
        permission"``.
    """
    status = f"HTTP {response.status_code}"
    try:
        body = response.json()
    except ValueError:
        return status
    if not isinstance(body, dict):
        return status
    error = body.get("error")
    if isinstance(error, dict):
        message = error.get("message") or error.get("status")
    else:
        message = body.get("error_description") or error
    return f"{status}: {message}" if message else status


def _post_form(url: str, data: dict) -> requests.Response:
    """
    Send a form POST to Google, turning network failures into ``ApiError``.

    Parameters
    ----------
    url : str
        Address to post to.
    data : dict
        Form fields. Sent in the body, never in the URL, so secrets don't
        end up in error messages.

    Returns
    -------
    requests.Response
        Google's response, whatever its status.

    Raises
    ------
    ApiError
        If Google could not be reached.
    """
    try:
        return requests.post(url, data=data, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise ApiError(f"Could not reach Google ({type(exc).__name__}). Check your internet connection.") from None


def _get_api(path: str, access_token: str, params: dict | None = None) -> dict:
    """
    Call a Google Health API endpoint and return its JSON.

    Parameters
    ----------
    path : str
        Path after ``/v4/users/me``, e.g. ``"/identity"``.
    access_token : str
        A valid access token.
    params : dict | None, optional
        Query parameters.

    Returns
    -------
    dict
        The decoded JSON response.

    Raises
    ------
    ApiError
        If Google can't be reached or answers with an error.
    """
    try:
        response = requests.get(
            API_URL + path,
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise ApiError(f"Could not reach Google Health ({type(exc).__name__}). Check your internet connection.") from None
    if not response.ok:
        raise ApiError(f"Google Health returned an error ({_google_error(response)}).")
    return response.json()


# ---- Connecting --------------------------------------------------------
def build_auth_url(user_id: int) -> str:
    """
    Create a Google login link for a user.

    A new random state is stored for the user and is valid for
    ``STATE_LIFETIME``. Call this only when the link is needed, because
    every call replaces the previous state.

    Parameters
    ----------
    user_id : int
        The logged-in user who wants to connect.

    Returns
    -------
    str
        The address of Google's consent page.

    Raises
    ------
    NotConfiguredError
        If the settings are missing.
    """
    config = _require_config()
    state = secrets.token_urlsafe(32)
    google_health_connection.set_oauth_state(user_id, state, datetime.now(UTC) + STATE_LIFETIME)
    query = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",  # ask for a refresh token
        "prompt": "consent",  # always ask, so Google always sends a refresh token
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(query)}"


def handle_callback(params: dict[str, str]) -> None:
    """
    Finish a login after Google redirects back to the app.

    The user is found by the ``state`` value (which is then cleared), the
    one-time ``code`` is swapped for tokens, and the account is checked
    with Google Health before the tokens are saved.

    Parameters
    ----------
    params : dict[str, str]
        The page's query parameters: ``state`` plus either ``code`` or
        ``error``.

    Raises
    ------
    GoogleHealthError
        With a message for the user if anything went wrong.
    """
    config = _require_config()
    pending = google_health_connection.consume_oauth_state(params.get("state", ""))
    if pending is None:
        raise GoogleHealthError(
            "This Google Health login link isn't recognised (it may already have been used). "
            "Go back to your AdamFit tab and try again."
        )
    if pending["is_expired"]:
        raise GoogleHealthError(
            "This Google Health login link has expired. Go back to your AdamFit tab, "
            "click **Refresh status** and then **Connect Google Health** again."
        )
    if "error" in params:
        if params["error"] == "access_denied":
            raise GoogleHealthError("Google Health was not connected because access was not allowed.")
        raise GoogleHealthError(f"Google returned an error: {params['error']}.")
    if not params.get("code"):
        raise GoogleHealthError("Google did not send a login code. Please try again.")

    response = _post_form(
        TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "code": params["code"],
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "redirect_uri": config["redirect_uri"],
        },
    )
    if not response.ok:
        raise ApiError(f"Google refused the login ({_google_error(response)}). Please try again.")
    tokens = response.json()
    granted_scopes = tokens.get("scope", "")
    if "refresh_token" not in tokens:
        raise GoogleHealthError("Google did not send a refresh token. Please try connecting again.")
    if WEIGHT_SCOPE not in granted_scopes.split():
        raise GoogleHealthError(
            "Google Health was not connected because permission to read health metrics "
            "(which includes weight) was not ticked. Connect again and allow it."
        )

    try:
        _get_api("/identity", tokens["access_token"])
    except ApiError as exc:
        raise GoogleHealthError(
            "Your Google account doesn't seem to be linked to Google Health. Open the Google Health "
            "app on your phone, check it is signed in with this Google account, then connect again. "
            f"({exc})"
        ) from None

    google_health_connection.save_tokens(
        pending["user_id"],
        tokens["refresh_token"],
        tokens["access_token"],
        datetime.now(UTC) + timedelta(seconds=int(tokens.get("expires_in", 3600))),
        granted_scopes,
    )


def get_access_token(user_id: int) -> str:
    """
    Return a working access token, refreshing it first if it is about to expire.

    If Google says the refresh token is no longer valid (in Testing mode
    they last 7 days), the tokens are cleared so the page shows the
    Connect button again.

    Parameters
    ----------
    user_id : int
        The user whose token is needed.

    Returns
    -------
    str
        An access token valid for at least ``TOKEN_EXPIRY_MARGIN``.

    Raises
    ------
    NotConnectedError
        If the user isn't connected or the connection has expired.
    ApiError
        If the refresh fails for another reason.
    """
    config = _require_config()
    stored = google_health_connection.get_tokens(user_id)
    if stored is None or stored["refresh_token"] is None:
        raise NotConnectedError(f"Google Health isn't connected. {RECONNECT_HINT}")

    expires_at = stored["access_token_expires_at"]
    if stored["access_token"] and expires_at and expires_at - TOKEN_EXPIRY_MARGIN > datetime.now(UTC):
        return stored["access_token"]

    response = _post_form(
        TOKEN_URL,
        {
            "grant_type": "refresh_token",
            "refresh_token": stored["refresh_token"],
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
        },
    )
    if not response.ok:
        if response.status_code in (400, 401) and "invalid_grant" in response.text:
            google_health_connection.clear_tokens(user_id)
            raise NotConnectedError(
                "Your Google Health connection has expired (while the Google Cloud app is in "
                f"Testing mode this happens every 7 days). {RECONNECT_HINT}"
            )
        raise ApiError(f"Could not refresh the Google Health login ({_google_error(response)}).")

    tokens = response.json()
    new_expiry = datetime.now(UTC) + timedelta(seconds=int(tokens.get("expires_in", 3600)))
    google_health_connection.save_access_token(user_id, tokens["access_token"], new_expiry)
    return tokens["access_token"]


def disconnect(user_id: int) -> None:
    """
    Disconnect a user: ask Google to cancel the login, then forget the tokens.

    Cancelling with Google is best-effort. The tokens are cleared even if
    Google can't be reached.

    Parameters
    ----------
    user_id : int
        The user to disconnect.
    """
    stored = google_health_connection.get_tokens(user_id)
    if stored is not None and stored["refresh_token"]:
        try:
            # Revoking the refresh token also cancels its access tokens
            requests.post(REVOKE_URL, data={"token": stored["refresh_token"]}, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException:
            pass
    google_health_connection.clear_tokens(user_id)


# ---- Weigh-ins ---------------------------------------------------------
def fetch_weight_points(access_token: str, start: date, end: date) -> list[dict]:
    """
    Download every weight data point between two dates, page by page.

    Parameters
    ----------
    access_token : str
        A valid access token.
    start : date
        First day to include.
    end : date
        Last day to include.

    Returns
    -------
    list[dict]
        The raw data points as Google returns them (newest first).

    Raises
    ------
    ApiError
        If Google can't be reached or answers with an error.
    """
    # The filter's upper bound is exclusive, so ask for "before the next day"
    day_after_end = end + timedelta(days=1)
    params = {
        "pageSize": PAGE_SIZE,
        "filter": (
            f'weight.sample_time.civil_time >= "{start.isoformat()}" '
            f'AND weight.sample_time.civil_time < "{day_after_end.isoformat()}"'
        ),
    }
    points = []
    while True:
        page = _get_api("/dataTypes/weight/dataPoints", access_token, params)
        points.extend(page.get("dataPoints", []))
        next_token = page.get("nextPageToken")
        if not next_token:
            return points
        params["pageToken"] = next_token


def _parse_offset(offset: str | None) -> timedelta:
    """
    Turn a Google duration such as ``"-14400s"`` into a timedelta.

    Parameters
    ----------
    offset : str | None
        Seconds followed by ``s``. None or unreadable values count as zero.

    Returns
    -------
    timedelta
        The offset from UTC.
    """
    try:
        return timedelta(seconds=float(str(offset).removesuffix("s")))
    except ValueError:
        return timedelta(0)


def parse_weight_point(point: dict) -> tuple[date, datetime, float] | None:
    """
    Read the local day, exact time and weight from one data point.

    The day is taken from ``civilTime`` (the clock time where the weigh-in
    happened) when Google sends it. Otherwise it is worked out from
    ``physicalTime`` plus ``utcOffset``.

    Parameters
    ----------
    point : dict
        One entry of the ``dataPoints`` list.

    Returns
    -------
    tuple[date, datetime, float] | None
        ``(day, physical_time, weight_kg)``, or None if the point has no
        weight or no time.
    """
    weight = point.get("weight") or {}
    sample_time = weight.get("sampleTime") or {}
    grams = weight.get("weightGrams")
    physical_text = sample_time.get("physicalTime")
    if grams is None or not physical_text:
        return None
    physical_time = datetime.fromisoformat(physical_text)
    if physical_time.tzinfo is None:
        # RFC 3339 times always have a zone, but be safe: treat a bare time as UTC
        physical_time = physical_time.replace(tzinfo=UTC)

    civil = sample_time.get("civilTime")
    civil_date = civil.get("date") if isinstance(civil, dict) else None
    if isinstance(civil_date, dict) and civil_date.get("year"):
        day = date(int(civil_date["year"]), int(civil_date["month"]), int(civil_date["day"]))
    elif isinstance(civil, str) and len(civil) >= 10:
        day = date.fromisoformat(civil[:10])
    else:
        offset = _parse_offset(sample_time.get("utcOffset"))
        day = (physical_time.astimezone(UTC) + offset).date()
    return day, physical_time, float(grams) / 1000


def latest_per_day(points: list[dict], start: date, end: date) -> dict[date, float]:
    """
    Keep only the latest weigh-in of each day within a date range.

    Parameters
    ----------
    points : list[dict]
        Raw data points from ``fetch_weight_points``, in any order.
    start : date
        First day to keep.
    end : date
        Last day to keep.

    Returns
    -------
    dict[date, float]
        Weight in kilograms keyed by day.
    """
    latest = {}  # day -> (physical_time, weight_kg)
    for point in points:
        parsed = parse_weight_point(point)
        if parsed is None:
            continue
        day, physical_time, weight_kg = parsed
        if not start <= day <= end:
            continue
        if day not in latest or physical_time > latest[day][0]:
            latest[day] = (physical_time, weight_kg)
    return {day: weight_kg for day, (_, weight_kg) in latest.items()}


def sync_weights(user_id: int, start: date, end: date) -> dict:
    """
    Copy weigh-ins from Google Health into AdamFit for a date range.

    Each synced day overwrites what is stored for that day, including
    weigh-ins typed in by hand. With several weigh-ins on one day, the
    latest one wins.

    Parameters
    ----------
    user_id : int
        The user to sync.
    start : date
        First day to sync.
    end : date
        Last day to sync (included).

    Returns
    -------
    dict
        ``weigh_ins`` (data points downloaded) and ``days_saved`` (days
        written to the database).

    Raises
    ------
    GoogleHealthError
        If the user isn't connected or Google returns an error.
    """
    access_token = get_access_token(user_id)
    points = fetch_weight_points(access_token, start, end)
    by_day = latest_per_day(points, start, end)
    weights.save_synced_weights(user_id, by_day)
    google_health_connection.mark_synced(user_id)
    return {"weigh_ins": len(points), "days_saved": len(by_day)}
