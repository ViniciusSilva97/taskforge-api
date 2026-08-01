from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserResponse


class UserNotFoundError(LookupError):
    pass


class UserEmailAlreadyExistsError(ValueError):
    pass


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = UserRepository(session)

    def create_user(self, data: UserCreate) -> UserResponse:
        if self.repository.get_by_email(str(data.email)):
            raise UserEmailAlreadyExistsError(
                f"Já existe um usuário cadastrado com o e-mail {data.email}."
            )

        user = self.repository.create(name=data.name, email=str(data.email))
        self.session.commit()
        return UserResponse.model_validate(user)

    def list_users(self) -> list[UserResponse]:
        return [UserResponse.model_validate(user) for user in self.repository.list()]

    def get_user(self, user_id: int) -> UserResponse:
        user = self.repository.get(user_id)
        if user is None:
            raise UserNotFoundError(f"Usuário {user_id} não encontrado.")
        return UserResponse.model_validate(user)
