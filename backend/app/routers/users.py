from fastapi import APIRouter, Depends, HTTPException, status
from typing import Literal

from dependencies import get_system
from system import System
from schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserProfileResponse,
    AuthResponse,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserRegisterRequest,
    system: System = Depends(get_system),
):
    """Register a new student or staff account."""
    target_list = system.student_list if payload.role == "student" else system.staff_list

    # Ensure username is unique within the role
    if any(u.username == payload.username for u in target_list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{payload.username}' is already taken.",
        )

    if payload.role == "student":
        student = system.add_student(
            username=payload.username,
            password=payload.password,
            student_id=payload.id_number,
        )
        if not student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student ID '{payload.id_number}' already exists.",
            )
        profile = UserProfileResponse(
            username=student.username,
            role="student",
            student_id=student.student_id,
            reserved_orders=student.reserved_orders,
        )
        return {"message": "Student registered successfully", "user": profile}

    else:
        staff = system.add_staff(
            username=payload.username,
            password=payload.password,
            staff_id=payload.id_number,
        )
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Staff ID '{payload.id_number}' already exists.",
            )
        profile = UserProfileResponse(
            username=staff.username,
            role="staff",
            staff_id=staff.staff_id,
        )
        return {"message": "Staff registered successfully", "user": profile}


@router.post("/login")
def login_user(
    payload: UserLoginRequest,
    system: System = Depends(get_system),
):
    """Checks the ID (and, for staff, the password) against the registered users."""
    user_id = payload.id.strip()

    if payload.role == "student":
        found = next((s for s in system.student_list if s.student_id == user_id), None)
        if not found:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid student ID",
            )
        return {"role": "student", "student_id": found.student_id}

    found = next((s for s in system.staff_list if s.staff_id == user_id), None)
    if not found or found.password != payload.password:
        # Same message for both so it doesn't reveal which staff IDs exist.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid staff ID or password",
        )
    return {"role": "staff", "staff_id": found.staff_id}


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    username: str,
    role: Literal["student", "staff"],
    system: System = Depends(get_system),
):
    """Fetch user profile details by username and role."""
    target_list = system.student_list if role == "student" else system.staff_list
    user = next((u for u in target_list if u.username == username), None)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found.",
        )

    if role == "student":
        return UserProfileResponse(
            username=user.username,
            role="student",
            student_id=user.student_id,
            reserved_orders=user.reserved_orders,
        )
    return UserProfileResponse(
        username=user.username,
        role="staff",
        staff_id=user.staff_id,
    )

@router.post("/student/notify")
def notify_student_endpoint(student_id: str):
    # 1. Check if one of student's reserved orders is marked old
    for order in system.old_list:
        if order.reserved_by == student_id:
    # 2. Create notification accordingly
            return {
                "needs_notif": True,
                "order_id": order.order_id,
                "message": "A previously reserved order has become old and is no longer available"
            }
    return {"needs_notif": False}