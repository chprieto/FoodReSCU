from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from system import System
from order import Status, Order
from user import Student

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

system = System()
student = system.add_student("student1", "password123", "STU001")

# Test Data
system.incoming_order("Burger")
system.incoming_order("Pizza")
system.incoming_order("Rice")

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
    return {
        "available": available_orders,
        "my_reservations": my_reservations,
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
    # 3. Call your system method
    success = system.reserve_order(order, student)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reserve order",
        )
    return {"message": "Order reserved successfully", "order_id": order.order_id}