"""
Accounts and saved reports.

The privacy property the rest of the app is built around - uploads are read in
memory and never written to disk - holds for logged-in users too. A SavedReport
stores the *rendered report*, not the resume: no file, no bytes, no extracted
text beyond what the report itself already displays. Deleting the report
deletes everything that was kept.
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

MIN_PASSWORD_LENGTH = 10


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    # Long enough for any werkzeug scheme; scrypt hashes are ~160 chars.
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                 default=_utcnow, server_default=func.now())

    reports: Mapped[list[SavedReport]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin",
        order_by="SavedReport.created_at.desc()")

    @staticmethod
    def normalise_email(email: str) -> str:
        return (email or "").strip().lower()

    def set_password(self, password: str) -> None:
        # werkzeug picks a salted, iterated scheme (scrypt by default); the raw
        # password is never held on the instance or written anywhere.
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password or "")

    def __repr__(self) -> str:                       # pragma: no cover - debugging aid
        return f"<User {self.email}>"


class SavedReport(db.Model):
    __tablename__ = "saved_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                         nullable=False, index=True)

    # What the report was about, for the list view. These are already visible on
    # the report itself; nothing new about the candidate is retained.
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category_label: Mapped[str] = mapped_column(String(120), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    strength: Mapped[float | None] = mapped_column(nullable=True)
    ats: Mapped[float | None] = mapped_column(nullable=True)
    jd_fit: Mapped[float | None] = mapped_column(nullable=True)
    overall: Mapped[float | None] = mapped_column(nullable=True)

    # The rendered report body - the fragment, not a whole page, so the header
    # is re-rendered live for whoever is looking at it.
    body: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                 default=_utcnow, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="reports")

    def __repr__(self) -> str:                       # pragma: no cover - debugging aid
        return f"<SavedReport {self.id} {self.title!r}>"
