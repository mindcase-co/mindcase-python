"""Typed response models for the Mindcase SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Parameter:
    """Agent parameter definition."""

    name: str
    key: str
    type: str
    required: bool = False
    description: str = ""
    default: Any = None
    options: Optional[List[Dict[str, str]]] = None

    @classmethod
    def from_dict(cls, key: str, data: dict) -> "Parameter":
        return cls(
            key=key,
            name=data.get("name", key),
            type=data.get("type", "string"),
            required=data.get("required", False),
            description=data.get("description", ""),
            default=data.get("default"),
            options=data.get("options"),
        )

    def __repr__(self) -> str:
        req = " (required)" if self.required else ""
        return f"Parameter({self.key}: {self.type}{req})"


@dataclass
class AgentSummary:
    """Agent summary returned by agents.list()."""

    group: str
    slug: str
    name: str
    description: str
    credits_per_row: int

    @property
    def path(self) -> str:
        """Agent path as 'group/slug'."""
        return f"{self.group}/{self.slug}"

    @classmethod
    def from_dict(cls, data: dict) -> "AgentSummary":
        return cls(
            group=data.get("group", ""),
            slug=data.get("slug", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            credits_per_row=data.get("credits_per_row", 1),
        )

    def __repr__(self) -> str:
        return f"Agent({self.path} — {self.credits_per_row} credits/row)"


@dataclass
class Agent:
    """Full agent details with parameter schema."""

    group: str
    slug: str
    name: str
    description: str
    credits_per_row: int
    parameters: Dict[str, Parameter] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        params = {}
        for key, info in data.get("parameters", {}).items():
            params[key] = Parameter.from_dict(key, info)
        return cls(
            group=data.get("group", ""),
            slug=data.get("slug", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            credits_per_row=data.get("credits_per_row", 1),
            parameters=params,
        )

    @property
    def required_params(self) -> Dict[str, Parameter]:
        """Only the required parameters."""
        return {k: v for k, v in self.parameters.items() if v.required}

    @property
    def optional_params(self) -> Dict[str, Parameter]:
        """Only the optional parameters."""
        return {k: v for k, v in self.parameters.items() if not v.required}

    def __repr__(self) -> str:
        req = [p.key for p in self.parameters.values() if p.required]
        return f"Agent({self.group}/{self.slug}, required={req})"


@dataclass
class Job:
    """Job status returned by run() and get_job()."""

    job_id: str
    agent: str
    status: str
    row_count: int = 0
    credits_used: int = 0
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        return cls(
            job_id=data.get("job_id", data.get("id", "")),
            agent=data.get("agent", ""),
            status=data.get("status", "unknown"),
            row_count=data.get("row_count", 0),
            credits_used=data.get("credits_used", 0),
            error=data.get("error"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            created_at=data.get("created_at"),
            expires_at=data.get("expires_at"),
        )

    @property
    def id(self) -> str:
        """Alias for job_id."""
        return self.job_id

    @property
    def is_running(self) -> bool:
        return self.status in ("queued", "running")

    @property
    def is_done(self) -> bool:
        return self.status in ("completed", "failed", "cancelled")

    @property
    def is_failed(self) -> bool:
        return self.status in ("failed", "cancelled")

    def __repr__(self) -> str:
        return f"Job({self.job_id[:12]}... {self.agent} [{self.status}] rows={self.row_count})"


@dataclass
class JobResults:
    """Results from a completed job."""

    status: str
    row_count: int
    data: List[Dict[str, Any]]

    @classmethod
    def from_dict(cls, data: dict) -> "JobResults":
        return cls(
            status=data.get("status", ""),
            row_count=data.get("row_count", 0),
            data=data.get("data", []),
        )

    @property
    def columns(self) -> List[str]:
        """Column names from the first row."""
        if self.data:
            return list(self.data[0].keys())
        return []

    def to_dicts(self) -> List[Dict[str, Any]]:
        """Return data as list of dicts (same as .data)."""
        return self.data

    def to_list(self, column: str) -> List[Any]:
        """Extract a single column as a flat list."""
        return [row.get(column) for row in self.data]

    def __repr__(self) -> str:
        cols = self.columns[:5]
        return f"JobResults({self.row_count} rows, columns={cols}{'...' if len(self.columns) > 5 else ''})"

    def __len__(self) -> int:
        return self.row_count

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, index):
        return self.data[index]
