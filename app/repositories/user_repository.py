from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, name: str, email: str, password_hash: str) -> User:
        user = User(
            name=name,
            email=email.lower(),
            password_hash=password_hash,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def get(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return self.session.scalar(statement)

    def list(self) -> list[User]:
        statement = select(User).order_by(User.id)
        return list(self.session.scalars(statement))
