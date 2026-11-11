import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin


class LLMProvider(enum.StrEnum):
    gemini = "gemini"
    claude = "claude"


class UserLLMKey(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_llm_keys"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_llm_keys_user_provider"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[LLMProvider] = mapped_column(Enum(LLMProvider, name="llm_provider"))
    encrypted_key: Mapped[str] = mapped_column(Text)
    last4: Mapped[str] = mapped_column(String(4))

    user: Mapped["User"] = relationship(back_populates="llm_keys")