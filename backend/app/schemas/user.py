from pydantic import BaseModel, Field
from typing import Literal, Optional, List
import uuid


class UserRegisterRequest(BaseModel):
    """Payload for creating a new student or staff account."""
    username: str = Field(..., min_length=1, description="Username for the new account")
    password: str = Field(..., min_length=1, description="Password for the new account")
    role: Literal["student", "staff"] = Field(..., description="Role of the user")
    id_number: Optional[str] = Field(None, description="Optional custom student_id or staff_id")


class UserLoginRequest(BaseModel):
    """Payload for user authentication."""
    role: Literal["student", "staff"]
    id: str
    password: str | None = None  # required for staff, not used for students


class UserProfileResponse(BaseModel):
    """Public profile information returned on login/registration."""
    username: str
    role: Literal["student", "staff"]
    student_id: Optional[str] = None
    staff_id: Optional[str] = None
    reserved_orders: Optional[List[uuid.UUID]] = None


class AuthResponse(BaseModel):
    """Response returned upon successful authentication or registration."""
    message: str
    user: UserProfileResponse
