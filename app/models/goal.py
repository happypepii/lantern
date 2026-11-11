import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin


class GoalStatus(enum.StrEnum):
    active = "active"
    completed = "completed"
    archived = "archived"


class Goal(IdMixin, TimestampMixin, Base):
    __tablename__ = "goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    background: Mapped[str] = mapped_column(Text)
    status: Mapped[GoalStatus] = mapped_column(
        Enum(GoalStatus, name="goal_status"), default=GoalStatus.active
    )

    user: Mapped["User"] = relationship(back_populates="goals")
    milestones: Mapped[list["Milestone"]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )