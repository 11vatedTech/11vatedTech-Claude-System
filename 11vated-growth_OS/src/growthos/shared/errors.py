"""Domain exception hierarchy.

The API layer maps these to HTTP responses; business logic never touches HTTP.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all GrowthOS domain errors."""


class NotFoundError(DomainError):
    """A referenced entity does not exist."""


class ValidationError(DomainError):
    """Input failed validation."""


class StateTransitionError(DomainError):
    """An illegal state transition was attempted."""

    def __init__(self, current: str, requested: str, machine: str) -> None:
        self.current = current
        self.requested = requested
        self.machine = machine
        super().__init__(
            f"Illegal transition in {machine}: {current!r} -> {requested!r}"
        )


class PermissionDeniedError(DomainError):
    """An action was denied by the autonomy policy engine."""


class ApprovalRequiredError(PermissionDeniedError):
    """An action requires founder approval before it may execute."""
