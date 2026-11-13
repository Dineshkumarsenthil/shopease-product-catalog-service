import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    """The logged-in user, taken from the JWT."""

    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role.lower() == settings.admin_role.lower()


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    """Checks the token and returns the user. Used by every protected route."""
    if credentials is None:
        raise _unauthorized("Bearer token missing")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            # the auth service may send the user id as a number, so skip the "sub must be text" check
            options={"verify_sub": False},
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token has expired")
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid token")

    user_id = payload.get(settings.jwt_user_id_claim)
    role = payload.get(settings.jwt_role_claim)
    if user_id is None or role is None:
        raise _unauthorized("Invalid token")

    return CurrentUser(user_id=str(user_id), role=str(role))


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Only lets administrators through."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
    return user
