import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin


class Milestone(IdMixin, TimestampMixin, Base):
    __tablename__ = "milestones"
    __table_args__ = (
        CheckConstraint("week_index >= 1", name="ck_milestones_week_index_positive"),
    )

    goal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), index=True
    )
    week_index: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    success_criteria: Mapped[str | None] = mapped_column(Text)

    goal: Mapped["Goal"] = relationship(back_populates="milestones")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="milestone",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )