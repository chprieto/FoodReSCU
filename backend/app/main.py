from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from system import System
from order import Status, Order
from user import Student
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReserveRequest(BaseModel):
    student_id: str

class ActivateRequest(BaseModel):
    staff_id: str

class DeleteRequest(BaseModel):
    staff_id: str

system = System()
student = system.add_student("student1", "password123", "STU001")

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

@app.post("/orders/{order_id}/activate")
def activate_order_endpoint(order_id: uuid.UUID, payload: ActivateRequest):
    # 1. Locate the upcoming order
    order = system.upcoming_list.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or no longer upcoming",
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
    # 3. Call the activate order system method
    success = system.activate_order(order, staff)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to activate order",
        )
    return {"message": "Order activated successfully", "order_id": order.order_id}

@app.post("/orders/{order_id}/delete")
def delete_order_endpoint(order_id: uuid.UUID, payload: DeleteRequest):
    # 1. Locate the order
    orderlist = system.find_orderlist(order_id)
    order = orderlist.get_order_by_id(order_id)
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
    return {"message": "Order deleted successfully", "order_id": order.order_id}
