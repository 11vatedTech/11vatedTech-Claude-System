"""SQLAlchemy declarative base and common mixins.

Enums are stored as constrained VARCHAR columns (not native Postgres enum
types) so migrations stay simple and reversible. The type annotation map lets
models declare ``Mapped[SomeEnum]`` directly.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from growthos.domain import enums as _enums
from growthos.shared.ids import new_id


def utcnow() -> datetime:
    return datetime.now(UTC)


def _enum_type(enum_cls: type[enum.Enum]) -> Enum:
    return Enum(
        enum_cls,
        native_enum=False,
        length=64,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )


def _build_type_map() -> dict:
    mapping: dict = {}
    for _name, member in vars(_enums).items():
        if isinstance(member, type) and issubclass(member, enum.Enum):
            mapping[member] = _enum_type(member)
    return mapping


class Base(DeclarativeBase):
    type_annotation_map = _build_type_map()


class IDMixin:
    """UUID primary key, generated application-side."""

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=new_id
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class Record(Base, IDMixin, TimestampMixin):
    """Base record with id + timestamps."""

    __abstract__ = True


# Convenience aliases for JSON columns.
jsonb = JSONB
