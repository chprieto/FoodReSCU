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

    def test_verify_registered_users(self):
        self.assertTrue(self.system.verify_student(self.student))
        self.assertTrue(self.system.verify_staff(self.staff))

    def test_verify_unknown_users(self):
        stranger = Student(username="ghost", password="nope", student_id="GHOST", reserved_orders=[])
        outsider = Staff(username="outsider", password="nope", staff_id="OUT")
        self.assertFalse(self.system.verify_student(stranger))
        self.assertFalse(self.system.verify_staff(outsider))

    def test_incoming_order_starts_upcoming(self):
        self.system.incoming_order("Chili")
        self.assertEqual(self.system.upcoming_list.get_length(), 1)
        stored = list(self.system.upcoming_list)[0]
        self.assertEqual(stored.item, "Chili")
        self.assertEqual(stored.status, Status.UPCOMING)

    def test_activate_order_success(self):
        order = Order(item="Chili", time_made=datetime.now() - timedelta(hours=1, minutes=5))
        self.system.upcoming_list.add_order(order)

        self.assertTrue(self.system.activate_order(order, self.staff))
        self.assertEqual(order.status, Status.ACTIVE)
        self.assertEqual(self.system.upcoming_list.get_length(), 0)
        self.assertEqual(self.system.active_list.get_order_by_id(order.order_id), order)

    def test_activate_order_unauthorized_staff(self):
        outsider = Staff(username="outsider", password="nope", staff_id="OUT")
        order = Order(item="Chili", time_made=datetime.now() - timedelta(hours=2))
        self.system.upcoming_list.add_order(order)

        self.assertFalse(self.system.activate_order(order, outsider))
        self.assertEqual(order.status, Status.UPCOMING)
        self.assertEqual(self.system.upcoming_list.get_length(), 1)
        self.assertEqual(self.system.active_list.get_length(), 0)

    def test_reserve_order_unknown_student(self):
        stranger = Student(username="ghost", password="nope", student_id="GHOST", reserved_orders=[])
        order = Order(item="Chili", status=Status.ACTIVE)
        self.system.active_list.add_order(order)

        self.assertFalse(self.system.reserve_order(order, stranger))
        self.assertEqual(order.status, Status.ACTIVE)
        self.assertIsNone(order.reserved_by)
        self.assertEqual(self.system.active_list.get_length(), 1)
        self.assertEqual(self.system.reserved_list.get_length(), 0)

    def test_pick_up_missing_from_reserved_list(self):
        order = Order(item="Chili", status=Status.RESERVED, reserved_by=self.student.student_id)
        self.student.reserved_orders.append(order.order_id)

        self.assertFalse(self.system.pick_up_order(order, self.student))
        self.assertEqual(order.status, Status.RESERVED)
        self.assertIn(order.order_id, self.student.reserved_orders)

    def test_second_reserve_rejected_while_first_is_open(self):
        # Verification compares the whole student record, which still has an
        # empty reservation list after the caller records the first order.
        first = Order(item="Chili", status=Status.ACTIVE)
        second = Order(item="Soup", status=Status.ACTIVE)
        self.system.active_list.add_order(first)
        self.system.active_list.add_order(second)

        self.assertTrue(self.system.reserve_order(first, self.student))
        self.assertFalse(self.system.reserve_order(second, self.student))
        self.assertEqual(second.status, Status.ACTIVE)
        self.assertEqual(self.system.active_list.get_length(), 1)
        self.assertEqual(len(self.student.reserved_orders), 1)

    def test_set_orders_as_old_moves_expired(self):
        expired = Order(
            item="Old Soup",
            time_made=datetime.now() - timedelta(hours=4),
            status=Status.ACTIVE,
        )
        self.system.active_list.add_order(expired)

        self.system.set_orders_as_old()

        self.assertEqual(expired.status, Status.OLD)
        self.assertEqual(self.system.active_list.get_length(), 0)
        self.assertEqual(self.system.old_list.get_order_by_id(expired.order_id), expired)

    def test_set_orders_as_old_keeps_recent(self):
        recent = Order(
            item="Fresh Soup",
            time_made=datetime.now() - timedelta(minutes=20),
            status=Status.ACTIVE,
        )
        self.system.active_list.add_order(recent)

        self.system.set_orders_as_old()

        self.assertEqual(recent.status, Status.ACTIVE)
        self.assertEqual(self.system.active_list.get_length(), 1)
        self.assertEqual(self.system.old_list.get_length(), 0)

    def test_large_batch_of_incoming_orders(self):
        for index in range(100):
            self.system.incoming_order(f"item-{index}")

        self.assertEqual(self.system.upcoming_list.get_length(), 100)
        self.assertEqual(self.system.active_list.get_length(), 0)
        stored = list(self.system.upcoming_list)
        self.assertEqual(stored[0].item, "item-0")
        self.assertEqual(stored[-1].item, "item-99")


if __name__ == "__main__":
    unittest.main()
