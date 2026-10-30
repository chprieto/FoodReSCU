from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from system import System
from order import Status, Order
from user import Student

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
    available_orders = list(system.active_list)
    my_reservations = [
        order for order in system.reserved_list 
        if order.reserved_by == student_id
    ]
    return {
        "available": available_orders,
        "my_reservations": my_reservations,
    }