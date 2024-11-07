from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: int
    username: str
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str