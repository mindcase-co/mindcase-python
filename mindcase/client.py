"""Mindcase API client."""

import os
import time
from typing import Any, Callable, Dict, Optional

__version__ = "0.4.0"

import requests

from mindcase.exceptions import (
    AuthenticationError,
    InsufficientCreditsError,
    MindcaseError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from mindcase.namespaces import AgentsNamespace, JobsNamespace, _parse_agent_path
from mindcase.types import Job, JobResults

_DEFAULT_BASE_URL = "https://api.mindcase.co/api/v1"
_DEFAULT_TIMEOUT = 30
_DEFAULT_POLL_INTERVAL = 3.0
_DEFAULT_RUN_TIMEOUT = 300
_ENV_KEY = "MINDCASE_API_KEY"


class Mindcase:
    """Client for the Mindcase Developer API.

    Usage:
        from mindcase import Mindcase

        client = Mindcase("mk_live_...")

        # Or set MINDCASE_API_KEY env var
        client = Mindcase()

        # Discover agents
        agents = client.agents.list("instagram")

        # Run an agent (sync — blocks until results)
        results = client.run("instagram/profiles", params={"usernames": ["nike"]})
        for row in results:
            print(row["Username"], row["Followers"])

        # Run async (returns immediately)
        job = client.run_async("instagram/profiles", params={"usernames": ["nike"]})
        print(job.id)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: int = _DEFAULT_TIMEOUT,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
        run_timeout: int = _DEFAULT_RUN_TIMEOUT,
    ):
        api_key = api_key or os.environ.get(_ENV_KEY)
        if not api_key:
            raise ValueError(
                "API key required. Pass api_key= or set the MINDCASE_API_KEY environment variable."
            )
        if not api_key.startswith("mk_live_"):
            raise ValueError("API key must start with 'mk_live_'")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._poll_interval = poll_interval
        self._run_timeout = run_timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"mindcase-python/{__version__}",
        })

        self.agents = AgentsNamespace(self)
        self.jobs = JobsNamespace(self)

    # ── Execution ────────────────────────────────────────────────────

    def run(
        self,
        agent: str,
        params: Dict[str, Any],
        timeout: Optional[int] = None,
        poll_interval: Optional[float] = None,
        on_status: Optional[Callable[[Job], None]] = None,
    ) -> JobResults:
        """Run an agent and wait for results (sync).

        Args:
            agent: Agent path as "group/slug" (e.g., "instagram/profiles")
            params: Agent-specific parameters
            timeout: Max seconds to wait (default: client's run_timeout)
            poll_interval: Seconds between polls (default: client's poll_interval)
            on_status: Optional callback called on each poll with the Job

        Returns:
            JobResults with status, row_count, data. Iterable and indexable.

        Example:
            results = client.run("instagram/profiles", params={"usernames": ["nike"]})
            for row in results:
                print(row["Username"], row["Followers"])
        """
        job = self.run_async(agent, params)
        return self._wait(
            job.job_id,
            timeout=timeout or self._run_timeout,
            poll_interval=poll_interval or self._poll_interval,
            on_status=on_status,
        )

    def run_async(self, agent: str, params: Dict[str, Any]) -> Job:
        """Start an agent job and return immediately.

        Args:
            agent: Agent path as "group/slug" (e.g., "instagram/profiles")
            params: Agent-specific parameters

        Returns:
            Job with job_id, agent, status, created_at

        Example:
            job = client.run_async("instagram/profiles", params={"usernames": ["nike"]})
            print(job.id)       # "job_abc123"
            print(job.status)   # "queued"
        """
        group, slug = _parse_agent_path(agent)
        data = self._post(f"/agents/{group}/{slug}/run", {"params": params})
        return Job.from_dict(data)

    # ── Credits ──────────────────────────────────────────────────────

    def credits(self) -> float:
        """Get remaining credit balance.

        Returns:
            Credits remaining (float)
        """
        data = self._get("/credits")
        return float(data.get("credits_remaining", 0))

    # ── Internal ─────────────────────────────────────────────────────

    def _wait(
        self,
        job_id: str,
        timeout: int,
        poll_interval: float,
        on_status: Optional[Callable[[Job], None]] = None,
    ) -> JobResults:
        """Poll a job until completion."""
        start = time.time()
        status = "unknown"
        while time.time() - start < timeout:
            job = self.jobs.get(job_id)
            status = job.status

            if on_status:
                on_status(job)

            if status == "completed":
                return self.jobs.results(job_id)

            if status in ("failed", "cancelled"):
                raise MindcaseError(
                    f"Job {status}: {job.error or 'Unknown error'}",
                    response={"job_id": job_id, "status": status},
                )

            time.sleep(poll_interval)

        raise MindcaseError(f"Job timed out after {timeout}s (last status: {status})")

    # ── HTTP Helpers ─────────────────────────────────────────────────

    _MAX_RETRIES = 3
    _RETRYABLE_STATUS = {500, 502, 503, 504}

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, body: Optional[dict] = None) -> dict:
        url = f"{self._base_url}{path}"
        last_exc: Optional[Exception] = None

        for attempt in range(self._MAX_RETRIES):
            try:
                if method == "GET":
                    r = self._session.get(url, params=params, timeout=self._timeout)
                elif method == "POST":
                    r = self._session.post(url, json=body, timeout=self._timeout)
                elif method == "DELETE":
                    r = self._session.delete(url, timeout=self._timeout)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                if r.status_code not in self._RETRYABLE_STATUS:
                    return self._handle_response(r)

                last_exc = MindcaseError(f"Server error {r.status_code}", status_code=r.status_code)

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_exc = MindcaseError(f"Network error: {e}")

            if attempt < self._MAX_RETRIES - 1:
                time.sleep(min(2 ** attempt, 8))

        raise last_exc or MindcaseError("Request failed after retries")

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> dict:
        return self._request("GET", path, params=params)

    def _post(self, path: str, body: dict) -> dict:
        return self._request("POST", path, body=body)

    def _delete(self, path: str) -> dict:
        return self._request("DELETE", path)

    def _handle_response(self, r: requests.Response) -> dict:
        try:
            data = r.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            data = {}

        if 200 <= r.status_code < 300:
            return data

        detail = data.get("detail", r.text)

        if r.status_code == 401:
            raise AuthenticationError(detail, status_code=401, response=data)
        elif r.status_code == 402:
            raise InsufficientCreditsError(detail, status_code=402, response=data)
        elif r.status_code == 404:
            raise NotFoundError(detail, status_code=404, response=data)
        elif r.status_code == 422:
            raise ValidationError(detail, status_code=422, response=data)
        elif r.status_code == 429:
            raise RateLimitError(detail, status_code=429, response=data)
        else:
            raise MindcaseError(detail, status_code=r.status_code, response=data)

    def __repr__(self) -> str:
        return f"Mindcase(key=****)"
