from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import TokenResponse


class InvalidCredentialsError(PermissionError):
    pass


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if (
            user is None
            or not user.is_active
            or not verify_password(password, user.password_hash)
        ):
            raise InvalidCredentialsError("E-mail ou senha inválidos.")
        return user

    def issue_token(self, user: User) -> TokenResponse:
        return TokenResponse(access_token=create_access_token(user.id))
