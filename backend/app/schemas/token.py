"""
Token Schema
"""
from pydantic import BaseModel


class Token(BaseModel):
    """JWT Token Schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token数据Schema"""
    username: str | None = None
    user_id: int | None = None
