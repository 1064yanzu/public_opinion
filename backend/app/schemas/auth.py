"""Auth-related schemas"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str
