"""Namespaced API groups for the Mindcase SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from mindcase.types import Agent, AgentSummary, Job, JobResults

if TYPE_CHECKING:
    from mindcase.client import Mindcase


class AgentsNamespace:
    """Agent discovery operations: client.agents.*"""

    def __init__(self, client: "Mindcase"):
        self._client = client

    def list(self, group: Optional[str] = None) -> List[AgentSummary]:
        """List agents, optionally filtered by group.

        Args:
            group: Filter to a specific group (e.g., "instagram").
                   If omitted, returns all agents across all groups.

        Returns:
            List of AgentSummary with group, slug, name, description, credits_per_row
        """
        if group:
            data = self._client._get(f"/agents/{group}")
            return [AgentSummary.from_dict({**a, "group": group}) for a in data.get("agents", [])]
        else:
            data = self._client._get("/agents/all")
            return [AgentSummary.from_dict(a) for a in data.get("agents", [])]

    def get(self, agent: str) -> Agent:
        """Get agent details including parameter schema.

        Args:
            agent: Agent path as "group/slug" (e.g., "instagram/profiles")

        Returns:
            Agent with name, description, parameters, credits_per_row
        """
        group, slug = _parse_agent_path(agent)
        data = self._client._get(f"/agents/{group}/{slug}")
        return Agent.from_dict(data)


class JobsNamespace:
    """Job management operations: client.jobs.*"""

    def __init__(self, client: "Mindcase"):
        self._client = client

    def list(self, status: Optional[str] = None, limit: int = 20) -> List[Job]:
        """List your jobs.

        Args:
            status: Optional filter (queued/running/completed/failed/cancelled)
            limit: Max jobs to return (default 20)

        Returns:
            List of Job objects
        """
        params: Dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        data = self._client._get("/jobs", params=params)
        return [Job.from_dict(j) for j in data.get("jobs", [])]

    def get(self, job_id: str) -> Job:
        """Get job status.

        Args:
            job_id: Job ID

        Returns:
            Job with id, agent, status, row_count, credits_used, etc.
        """
        data = self._client._get(f"/jobs/{job_id}")
        return Job.from_dict(data)

    def results(self, job_id: str) -> JobResults:
        """Get job results (collected data).

        Args:
            job_id: Job ID

        Returns:
            JobResults with status, row_count, data. Iterable and indexable.
        """
        data = self._client._get(f"/jobs/{job_id}/results")
        return JobResults.from_dict(data)

    def cancel(self, job_id: str) -> Job:
        """Cancel a running job. Credits are not charged for cancelled jobs.

        Args:
            job_id: Job ID to cancel
        """
        data = self._client._delete(f"/jobs/{job_id}")
        return Job.from_dict(data)


def _parse_agent_path(agent: str) -> tuple:
    """Parse 'group/slug' into (group, slug)."""
    parts = agent.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Agent path must be 'group/slug', got: '{agent}'")
    return parts[0], parts[1]
