import os
import sys
import unittest
from datetime import datetime, timedelta

# Ensure backend/app directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from system import System
from order import Order, Status
from user import Student, Staff


class TestSystem(unittest.TestCase):

    def setUp(self):
        self.system = System()
        self.student = Student(username="student1", password="password123", student_id="STU001", reserved_orders=[])
        self.system.add_student("student1", "password123", "STU001")
        self.staff = Staff(username="staff1", password="password123", staff_id="STAFF001")
        self.system.add_staff("staff1", "password123", "STAFF001")

    # 1. Normal Case: Student successfully reserves an active order
    def test_reserve_order_success(self):
        order = Order(item="Burger", status=Status.ACTIVE)
        self.system.active_list.add_order(order)

        result = self.system.reserve_order(order, self.student)

        self.assertTrue(result)
        self.assertEqual(order.status, Status.RESERVED)
        self.assertEqual(order.reserved_by, self.student.student_id)
        self.assertIsNotNone(order.time_reserved)
        self.assertIn(order.order_id, self.student.reserved_orders)
        self.assertEqual(self.system.active_list.get_length(), 0)
        self.assertEqual(self.system.reserved_list.get_length(), 1)
        self.assertEqual(self.system.reserved_list.get_order_by_id(order.order_id), order)

    # 2. Normal Case: Student successfully picks up their reserved order
    def test_pick_up_order_success(self):
        order = Order(item="Fries", status=Status.ACTIVE)
        self.system.active_list.add_order(order)
        self.system.reserve_order(order, self.student)

        result = self.system.pick_up_order(order, self.student)

        self.assertTrue(result)
        self.assertEqual(order.status, Status.PICKED_UP)
        self.assertNotIn(order.order_id, self.student.reserved_orders)
        self.assertEqual(self.system.reserved_list.get_length(), 0)
        self.assertEqual(self.system.picked_up_list.get_length(), 1)
        self.assertEqual(self.system.picked_up_list.get_order_by_id(order.order_id), order)

    # 3. Known Incorrect Case: Unauthorized student attempts to pick up someone else's order
    def test_pick_up_order_unauthorized_student(self):
        other_student = Student(username="student2", password="password456", student_id="STU002", reserved_orders=[])
        self.system.add_student("student2", "password456", "STU002")

        order = Order(item="Pizza", status=Status.ACTIVE)
        self.system.active_list.add_order(order)
        self.system.reserve_order(order, self.student)

        # other_student attempts to pick up self.student's order
        result = self.system.pick_up_order(order, other_student)

        self.assertFalse(result)
        self.assertEqual(order.status, Status.RESERVED)
        self.assertEqual(order.reserved_by, self.student.student_id)
        self.assertIn(order.order_id, self.student.reserved_orders)
        self.assertNotIn(order.order_id, other_student.reserved_orders)
        self.assertEqual(self.system.reserved_list.get_length(), 1)
        self.assertEqual(self.system.picked_up_list.get_length(), 0)

    # 4. Known Incorrect Case: Attempting to reserve an order not found in the active_list
    def test_reserve_order_not_in_active_list(self):
        order = Order(item="Salad", status=Status.ACTIVE)
        # Note: order is never added to active_list

        result = self.system.reserve_order(order, self.student)

        self.assertFalse(result)
        self.assertEqual(self.system.reserved_list.get_length(), 0)
        self.assertNotIn(order.order_id, self.student.reserved_orders)
        self.assertIsNone(order.reserved_by)

    # 5. Edge Case: Boundary condition where order is too new to be activated (< 1 hour threshold)
    def test_activate_order_too_early(self):
        recent_time = datetime.now() - timedelta(minutes=15)
        order = Order(item="Sandwich", time_made=recent_time, status=Status.UPCOMING)
        self.system.upcoming_list.add_order(order)

        result = self.system.activate_order(order, self.staff)

        self.assertFalse(result)
        self.assertEqual(order.status, Status.UPCOMING)
        self.assertEqual(self.system.upcoming_list.get_length(), 1)
        self.assertEqual(self.system.active_list.get_length(), 0)


if __name__ == "__main__":
    unittest.main()
