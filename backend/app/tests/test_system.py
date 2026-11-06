import os
import sys
import unittest
import uuid
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
        self.added_student = self.system.add_student("student1", "password123", "STU001")
        self.staff = Staff(username="staff1", password="password123", staff_id="STAFF001")
        self.added_staff = self.system.add_staff("staff1", "password123", "STAFF001")

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
        added_other = self.system.add_student("student2", "password456", "STU002")
        self.assertIsNotNone(added_other)
        self.assertEqual(added_other.student_id, "STU002")

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
        self.assertIsNotNone(self.added_student)
        self.assertIsNotNone(self.added_staff)
        self.assertEqual(self.added_student.student_id, "STU001")
        self.assertEqual(self.added_staff.staff_id, "STAFF001")

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

    # =========================================================================
    # Tests for new add_student and add_staff features
    # =========================================================================

    # Normal Case: add_student returns the created Student object and adds it to student_list
    def test_add_student_success_returns_student(self):
        new_student = self.system.add_student("alex", "pass123", "STU099")
        self.assertIsNotNone(new_student)
        self.assertIsInstance(new_student, Student)
        self.assertEqual(new_student.username, "alex")
        self.assertEqual(new_student.password, "pass123")
        self.assertEqual(new_student.student_id, "STU099")
        self.assertIn(new_student, self.system.student_list)
        self.assertTrue(self.system.verify_student(new_student))

    # Normal Case: add_staff returns the created Staff object and adds it to staff_list
    def test_add_staff_success_returns_staff(self):
        new_staff = self.system.add_staff("jordan", "pass456", "STAFF099")
        self.assertIsNotNone(new_staff)
        self.assertIsInstance(new_staff, Staff)
        self.assertEqual(new_staff.username, "jordan")
        self.assertEqual(new_staff.password, "pass456")
        self.assertEqual(new_staff.staff_id, "STAFF099")
        self.assertIn(new_staff, self.system.staff_list)
        self.assertTrue(self.system.verify_staff(new_staff))

    # Known Incorrect Case: duplicate student_id rejected and returns None
    def test_add_student_duplicate_id_rejected(self):
        initial_count = len(self.system.student_list)
        duplicate = self.system.add_student("imposter", "otherpass", "STU001")
        self.assertIsNone(duplicate)
        self.assertEqual(len(self.system.student_list), initial_count)
        # Ensure original student data is preserved
        existing = next(s for s in self.system.student_list if s.student_id == "STU001")
        self.assertEqual(existing.username, "student1")

    # Known Incorrect Case: duplicate staff_id rejected and returns None
    def test_add_staff_duplicate_id_rejected(self):
        initial_count = len(self.system.staff_list)
        duplicate = self.system.add_staff("imposter", "otherpass", "STAFF001")
        self.assertIsNone(duplicate)
        self.assertEqual(len(self.system.staff_list), initial_count)
        # Ensure original staff data is preserved
        existing = next(s for s in self.system.staff_list if s.staff_id == "STAFF001")
        self.assertEqual(existing.username, "staff1")

    # Edge Case: student_id=None automatically generates a valid 32-character hex UUID
    def test_add_student_auto_generates_id_when_none(self):
        student = self.system.add_student("auto_student", "autopass", None)
        self.assertIsNotNone(student)
        self.assertIsInstance(student, Student)
        self.assertEqual(student.username, "auto_student")
        self.assertIsInstance(student.student_id, str)
        self.assertEqual(len(student.student_id), 32)
        # Verify valid UUID hex format
        parsed_uuid = uuid.UUID(hex=student.student_id)
        self.assertEqual(parsed_uuid.hex, student.student_id)
        self.assertIn(student, self.system.student_list)
        self.assertTrue(self.system.verify_student(student))

    # Edge Case: staff_id=None automatically generates a valid 32-character hex UUID
    def test_add_staff_auto_generates_id_when_none(self):
        staff = self.system.add_staff("auto_staff", "autopass", None)
        self.assertIsNotNone(staff)
        self.assertIsInstance(staff, Staff)
        self.assertEqual(staff.username, "auto_staff")
        self.assertIsInstance(staff.staff_id, str)
        self.assertEqual(len(staff.staff_id), 32)
        # Verify valid UUID hex format
        parsed_uuid = uuid.UUID(hex=staff.staff_id)
        self.assertEqual(parsed_uuid.hex, staff.staff_id)
        self.assertIn(staff, self.system.staff_list)
        self.assertTrue(self.system.verify_staff(staff))

    # Edge Case: omitting student_id / staff_id uses default None and generates UUID
    def test_add_user_with_omitted_id_parameter(self):
        student = self.system.add_student("omitted_stu", "pass123")
        staff = self.system.add_staff("omitted_stf", "pass456")
        self.assertIsNotNone(student)
        self.assertIsNotNone(staff)
        self.assertEqual(len(student.student_id), 32)
        self.assertEqual(len(staff.staff_id), 32)
        self.assertIn(student, self.system.student_list)
        self.assertIn(staff, self.system.staff_list)

    # Edge Case: multiple auto-generated IDs are unique
    def test_add_multiple_auto_id_users_generate_unique_ids(self):
        student_a = self.system.add_student("user_a", "pass_a", None)
        student_b = self.system.add_student("user_b", "pass_b", None)
        staff_a = self.system.add_staff("staff_a", "pass_a", None)
        staff_b = self.system.add_staff("staff_b", "pass_b", None)

        self.assertNotEqual(student_a.student_id, student_b.student_id)
        self.assertNotEqual(staff_a.staff_id, staff_b.staff_id)
        self.assertEqual(len(self.system.student_list), 3)  # setUp student + 2 auto
        self.assertEqual(len(self.system.staff_list), 3)    # setUp staff + 2 auto

    def test_find_orderlist(self):
        order1 = Order(item="Burger", status=Status.ACTIVE)
        order2 = Order(item="Fries", status=Status.OLD)
        order3 = Order(item="Drink", status = Status.RESERVED)
        self.system.active_list.add_order(order1)
        self.system.old_list.add_order(order2)
        self.assertEqual(self.system.upcoming_list.get_length(), 0)
        self.assertEqual(self.system.active_list.get_length(), 1)
        self.assertEqual(self.system.reserved_list.get_length(), 0)
        self.assertEqual(self.system.picked_up_list.get_length(), 0)
        self.assertEqual(self.system.old_list.get_length(), 1)
        result1 = self.system.find_orderlist(order1.order_id)
        self.assertEqual(result1, self.system.active_list)
        result2 = self.system.find_orderlist(order2.order_id)
        self.assertEqual(result2, self.system.old_list)
        result3 = self.system.find_orderlist(order3.order_id)
        self.assertEqual(result3, None)


if __name__ == "__main__":
    unittest.main()
