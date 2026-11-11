import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin


class TaskStatus(enum.StrEnum):
    todo = "todo"
    doing = "doing"
    done = "done"


class Task(IdMixin, TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("estimate_hours >= 0", name="ck_tasks_estimate_hours_nonneg"),
        CheckConstraint(
            "(status = 'done') = (completed_at IS NOT NULL)",
            name="ck_tasks_done_iff_completed_at",
        ),
    )

    milestone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("milestones.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"), default=TaskStatus.todo
    )
    estimate_hours: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    milestone: Mapped["Milestone"] = relationship(back_populates="tasks")