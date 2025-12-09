# app/auth/dependencies.py

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User
from app.schemas.user import UserResponse


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


from sqlalchemy.orm import Session
from app.database import get_db

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Dependency to get current user from JWT token in header or cookie."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = None
    # Try to get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    # If not in header, try cookie
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception

    user_id = User.verify_token(token)
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return UserResponse.model_validate(user)


def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Dependency to get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user
