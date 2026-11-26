from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from system import System
from order import Status, Order
from user import Student
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Literal

from dependencies import system, get_system
from routers import orders, users
from schemas.order import ReserveRequest, ActivateRequest, DeleteRequest

app = FastAPI(
    title="FoodReSCU API",
    description="API for FoodReSCU leftover food ordering and reservation management.",
    version="1.0.0",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    # Any local dev port works (Vite moves to 5174, 5175... when 5173 is busy).
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    role: Literal["student", "staff"]
    id: str
    password: str | None = None  # required for staff, not used for students

class ReserveRequest(BaseModel):
    student_id: str

class ActivateRequest(BaseModel):
    staff_id: str

class DeleteRequest(BaseModel):
    staff_id: str

class CreateRequest(BaseModel):
    staff_id: str
    item: str
    age_hours: int = 0
    age_minutes: int = 0

system = System()
student = system.add_student("student1", "password123", "STU001")
# Demo staff account: sign in with staff ID STAFF001 / password staff123
system.add_staff("staff1", "staff123", "STAFF001")

# Test Data
system.incoming_order("Burger")
system.incoming_order("Pizza")
system.incoming_order("Rice")

# Already-claimable orders (made 70 min ago) so students have something to reserve while testing
for item in ("Pasta", "Salad", "Sandwich"):
    system.active_list.add_order(
        Order(item=item, status=Status.ACTIVE, time_made=datetime.now() - timedelta(minutes=70))
    )

order = Order(item="Burger", status=Status.ACTIVE)
system.active_list.add_order(order)
system.reserve_order(order, student)


@app.post("/login")
def login(payload: LoginRequest):
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


@app.get("/staff/orders")
def get_staff_orders():
    """Returns all orders grouped into divisions for the staff dashboard."""
    system.refresh_order_statuses()
    return {
        "upcoming": list(system.upcoming_list),
        "active": list(system.active_list),
        "reserved": list(system.reserved_list),
        "picked_up": list(system.picked_up_list),
        "old": list(system.old_list),
    }

@app.get("/student/orders")
def get_student_orders(student_id: str):
    """Returns only available orders and orders reserved by this student."""
    system.refresh_order_statuses()
    available_orders = list(system.active_list)
    my_reservations = [
        order for order in system.reserved_list 
        if order.reserved_by == student_id
    ]
    # Keep orders they already collected so they don't vanish from "Your orders".
    my_picked_up = [
        order for order in system.picked_up_list
        if order.reserved_by == student_id
    ]
    return {
        "available": available_orders,
        "my_reservations": my_reservations,
        "my_picked_up": my_picked_up,
    }

@app.post("/orders/{order_id}/reserve")
def reserve_order_endpoint(order_id: uuid.UUID, payload: ReserveRequest):
    # 1. Locate the active order
    order = system.active_list.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or no longer active for reservation",
        )
    # 2. Locate the student
    student = next(
        (s for s in system.student_list if s.student_id == payload.student_id),
        None,
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{payload.student_id}' not found",
        )
    # 3. Call the reserve order system method
    success = system.reserve_order(order, student)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reserve order",
        )
    return {"message": "Order reserved successfully", "order_id": order.order_id}

@app.post("/orders/{order_id}/pickup")
def pick_up_order_endpoint(order_id: uuid.UUID, payload: ReserveRequest):
    # 1. Locate the reserved order
    order = system.reserved_list.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or not currently reserved",
        )
    # 2. Locate the student
    student = next(
        (s for s in system.student_list if s.student_id == payload.student_id),
        None,
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID '{payload.student_id}' not found",
        )
    # 3. Only the student who reserved it may pick it up
    success = system.pick_up_order(order, student)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This order is not reserved by you, kid. Sorry.",
        )
    return {"message": "Order picked up successfully", "order_id": order.order_id}


@app.post("/orders/{order_id}/delete")
def delete_order_endpoint(order_id: uuid.UUID, payload: DeleteRequest):
    # 1. Locate the order
    orderlist = system.find_orderlist(order_id)
    order = orderlist.get_order_by_id(order_id) if orderlist else None
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or no longer in the system",
        )
    # 2. Locate the staff
    staff = next(
        (s for s in system.staff_list if s.staff_id == payload.staff_id),
        None,
    )
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with ID '{payload.staff_id}' not found",
        )
    # 3. Call the remove order method
    success = orderlist.remove_order(order)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete order",
        )
    # If a student had reserved it, drop it from their reservations too
    for s in system.student_list:
        if order.order_id in s.reserved_orders:
            s.reserved_orders.remove(order.order_id)
    return {"message": "Order deleted successfully", "order_id": order.order_id}

@app.post("/student/notify")
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

@app.post("/staff/create_order")
def create_order_endpoint(payload: CreateRequest):
    # 1. Verify staff member
    staff = next(
        (s for s in system.staff_list if s.staff_id == payload.staff_id),
        None,
    )
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with ID '{payload.staff_id}' not found",
        )
    # 2. Create the new order
    order_age = payload.age_miuntes + (60 * payload.age_hours)
    new_order = Order(item=payload.item, time_made = datetime.now() - timedelta(minutes=order_age))
    system.upcoming_list.add_order(new_order)
    return {"message": "Order created successfully", "order_id": new_order.order_id}
