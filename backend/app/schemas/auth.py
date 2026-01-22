from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    full_name: str | None = None
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True

# ✅ NEW: login returns token + user


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
