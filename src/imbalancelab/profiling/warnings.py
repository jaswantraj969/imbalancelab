"""Heuristic findings. These are suspicions backed by a statistic, never proof."""

from typing import Any, Literal

from pydantic import BaseModel, Field

Severity = Literal["info", "warning"]


class ProfileWarning(BaseModel):
    """A heuristic finding about the data.

    ``message`` is worded as a suspicion ("suspected", "possible"). ``evidence`` carries the
    statistic that triggered it, so a reader can judge it for themselves.
    """

    code: str
    column: str | None = None
    severity: Severity = "warning"
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)
