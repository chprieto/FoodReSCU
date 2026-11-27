import uuid
from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_system
from system import System
from schemas.order import (
    ReserveOrderRequest,
    PickupOrderRequest,
    ActivateOrderRequest,
    DeleteOrderRequest,
    OrderActionResponse,
    StaffOrdersResponse,
    StudentOrdersResponse,
    CreateRequest,
)

router = APIRouter(tags=["Orders"])


# -------------------------------------------------------------
# Query Endpoints (Fetch orders)
# -------------------------------------------------------------

@router.get("/orders/staff", response_model=StaffOrdersResponse)
@router.get("/staff/orders", response_model=StaffOrdersResponse, include_in_schema=False)
def get_staff_orders(system: System = Depends(get_system)):
    """Returns all orders grouped into divisions for the staff dashboard."""
    system.refresh_order_statuses()
    return {
        "upcoming": list(system.upcoming_list),
        "active": list(system.active_list),
        "reserved": list(system.reserved_list),
        "picked_up": list(system.picked_up_list),
        "old": list(system.old_list),
    }


@router.get("/orders/student", response_model=StudentOrdersResponse)
@router.get("/student/orders", response_model=StudentOrdersResponse, include_in_schema=False)
def get_student_orders(student_id: str, system: System = Depends(get_system)):
    """Returns only available orders and orders reserved by this student."""
    system.refresh_order_statuses()
    available_orders = list(system.active_list)
    my_reservations = [
        order for order in system.reserved_list
        if order.reserved_by == student_id
    ]
    my_picked_up = [
        order for order in system.picked_up_list
        if order.reserved_by == student_id
    ]
    return {
        "available": available_orders,
        "my_reservations": my_reservations,
        "my_picked_up": my_picked_up,
    }


# -------------------------------------------------------------
# Mutation Endpoints (Actions on specific orders)
# -------------------------------------------------------------

@router.post("/orders/{order_id}/reserve", response_model=OrderActionResponse)
def reserve_order_endpoint(
    order_id: uuid.UUID,
    payload: ReserveOrderRequest,
    system: System = Depends(get_system),
):
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


@router.post("/orders/{order_id}/pickup", response_model=OrderActionResponse)
def pick_up_order_endpoint(
    order_id: uuid.UUID,
    payload: PickupOrderRequest,
    system: System = Depends(get_system),
):
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


@router.post("/orders/{order_id}/activate", response_model=OrderActionResponse)
def activate_order_endpoint(
    order_id: uuid.UUID,
    payload: ActivateOrderRequest,
    system: System = Depends(get_system),
):
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


@router.post("/orders/{order_id}/delete", response_model=OrderActionResponse)
def delete_order_endpoint(
    order_id: uuid.UUID,
    payload: DeleteOrderRequest,
    system: System = Depends(get_system),
):
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

    return {"message": "Order deleted successfully", "order_id": order.order_id}


@router.post("/staff/create_order")
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
    order_age = payload.age_minutes + (60 * payload.age_hours)
    new_order = Order(item=payload.item, time_made = datetime.now() - timedelta(minutes=order_age))
    system.upcoming_list.add_order(new_order)
    return {"message": "Order created successfully", "order_id": new_order.order_id}
