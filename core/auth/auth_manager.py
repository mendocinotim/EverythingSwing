from datetime import datetime, timedelta
from typing import Optional, List
from .models import User, UserCreate, UserUpdate, Token
from .jwt_handler import JWTHandler

class AuthManager:
    def __init__(self, jwt_handler: JWTHandler):
        self.jwt_handler = jwt_handler
        # In a real application, this would be a database
        self.users: List[User] = []
        self.user_id_counter = 1

    def create_user(self, user_create: UserCreate) -> User:
        # Check if user already exists
        if any(u.email == user_create.email for u in self.users):
            raise ValueError("Email already registered")
        if any(u.username == user_create.username for u in self.users):
            raise ValueError("Username already taken")

        # Create new user
        hashed_password = self.jwt_handler.get_password_hash(user_create.password)
        user = User(
            id=self.user_id_counter,
            email=user_create.email,
            username=user_create.username,
            full_name=user_create.full_name,
            is_active=user_create.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.users.append(user)
        self.user_id_counter += 1
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = next((u for u in self.users if u.username == username), None)
        if not user:
            return None
        if not self.jwt_handler.verify_password(password, user.password):
            return None
        return user

    def create_access_token(self, user: User) -> Token:
        access_token_expires = timedelta(minutes=self.jwt_handler.access_token_expire_minutes)
        access_token = self.jwt_handler.create_access_token(
            data={"sub": user.username, "email": user.email},
            expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")

    def get_user(self, user_id: int) -> Optional[User]:
        return next((u for u in self.users if u.id == user_id), None)

    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        user = self.get_user(user_id)
        if not user:
            return None

        update_data = user_update.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["password"] = self.jwt_handler.get_password_hash(update_data["password"])
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        return user

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        self.users.remove(user)
        return True 