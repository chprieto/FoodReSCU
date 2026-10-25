import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pydantic import ValidationError

from order import ACTIVE_TIME, OLD_TIME, Order, OrderList, Status


class TestOrder(unittest.TestCase):

    def test_default_order_values(self):
        order = Order(item="Burger")
        self.assertEqual(order.item, "Burger")
        self.assertEqual(order.status, Status.UPCOMING)
        self.assertIsNotNone(order.order_id)
        self.assertIsNone(order.time_reserved)

    def test_order_activation_eligible(self):
        # Create an order made 1.5 hours ago (ACTIVE_TIME threshold is 1 hour)
        past_time = datetime.now() - timedelta(minutes=90)
        order = Order(item="Fries", time_made=past_time)

        order.activate()
        self.assertEqual(order.status, Status.ACTIVE)

    def test_order_activation_too_early(self):
        # Order made just 10 minutes ago
        recent_time = datetime.now() - timedelta(minutes=10)
        order = Order(item="Fries", time_made=recent_time)

        order.activate()
        self.assertEqual(order.status, Status.UPCOMING)

    def test_order_reservation(self):
        past_time = datetime.now() - timedelta(minutes=90)
        order = Order(item="Burger", time_made=past_time, status=Status.ACTIVE)

        order.reserve("07700008361")
        self.assertEqual(order.status, Status.RESERVED)
        self.assertEqual(order.reserved_by, "07700008361")
        self.assertIsNotNone(order.time_reserved)

    def test_set_old(self):
        active_time = datetime.now() - timedelta(minutes=90)
        old_time = datetime.now() - timedelta(hours=3)
        
        order1 = Order(item="Burger", time_made=old_time, status=Status.ACTIVE)
        order2 = Order(item="Burger", time_made=old_time, status=Status.PICKED_UP)
        order3 = Order(item="Burger", time_made=active_time, status=Status.ACTIVE)

        order1.set_old()
        self.assertEqual(order1.status, Status.OLD)

        order2.set_old()
        self.assertEqual(order2.status, Status.PICKED_UP)

        order3.set_old()
        self.assertEqual(order3.status, Status.ACTIVE)

    def test_time_active_for_past_order(self):
        order = Order(item="Soup", time_made=datetime.now() - timedelta(hours=2))
        elapsed = order.get_time_active()
        self.assertGreaterEqual(elapsed, timedelta(hours=2))
        self.assertLess(elapsed, timedelta(hours=2, minutes=1))

    def test_activate_at_one_hour_boundary(self):
        order = Order(item="Soup", time_made=datetime.now() - ACTIVE_TIME)
        self.assertTrue(order.activate())
        self.assertEqual(order.status, Status.ACTIVE)

    def test_activate_rejects_non_upcoming_status(self):
        order = Order(
            item="Soup",
            time_made=datetime.now() - timedelta(hours=5),
            status=Status.ACTIVE,
        )
        self.assertFalse(order.activate())
        self.assertEqual(order.status, Status.ACTIVE)

    def test_reserve_rejects_non_active_status(self):
        order = Order(item="Soup", status=Status.UPCOMING)
        self.assertFalse(order.reserve("STU001"))
        self.assertEqual(order.status, Status.UPCOMING)
        self.assertIsNone(order.reserved_by)
        self.assertIsNone(order.time_reserved)

    def test_pick_up_only_from_reserved(self):
        reserved = Order(item="Soup", status=Status.RESERVED, reserved_by="STU001")
        active = Order(item="Soup", status=Status.ACTIVE)

        self.assertTrue(reserved.pick_up())
        self.assertEqual(reserved.status, Status.PICKED_UP)
        self.assertFalse(active.pick_up())
        self.assertEqual(active.status, Status.ACTIVE)

    def test_set_old_at_three_hour_boundary(self):
        order = Order(
            item="Soup",
            time_made=datetime.now() - OLD_TIME,
            status=Status.ACTIVE,
        )
        self.assertTrue(order.set_old())
        self.assertEqual(order.status, Status.OLD)

    def test_edge_empty_item_name(self):
        order = Order(item="")
        self.assertEqual(order.item, "")
        self.assertEqual(order.status, Status.UPCOMING)

    def test_invalid_none_item(self):
        with self.assertRaises(ValidationError):
            Order(item=None)

    def test_invalid_wrong_item_type(self):
        with self.assertRaises(ValidationError):
            Order(item=25)

    def test_invalid_bad_status_value(self):
        with self.assertRaises(ValidationError):
            Order(item="Soup", status="COOKED")


class TestOrderList(unittest.TestCase):

    def setUp(self):
        self.active_list = OrderList(expected_status=Status.ACTIVE)

    # tests adding an order works correctly
    def test_add_order_with_matching_status(self):
        order = Order(item="Wrap", status=Status.ACTIVE)
        self.active_list.add_order(order)
        self.assertEqual(self.active_list.get_length(), 1)

    # tests you cannot add an order not part of accepted statuses
    def test_add_order_with_mismatched_status(self):
        order = Order(item="Wrap", status=Status.UPCOMING)
        self.active_list.add_order(order)
        self.assertEqual(self.active_list.get_length(), 0)

    # tests removing an order
    def test_remove_order(self):
        order = Order(item="Wrap", status=Status.ACTIVE)
        self.active_list.add_order(order)
        
        self.assertEqual(self.active_list.get_length(), 1)
        self.assertEqual(self.active_list.remove_order(order), order)
        self.assertEqual(self.active_list.get_length(), 0)

    # tests removing an order not present is handeled correctly  
    def test_remove_nonexistant_order(self):
        order1 = Order(item="Wrap", status=Status.ACTIVE)
        order2 = Order(item="Burger", status=Status.ACTIVE)

        self.active_list.add_order(order1)
        self.assertEqual(self.active_list.get_length(), 1)

        self.assertIsNone(self.active_list.remove_order(order2))
        self.assertEqual(self.active_list.get_length(), 1)

    # tests getting both an order that is part of a list, and behavior if it is not
    def test_get_order_by_id(self):
        order1 = Order(item="Wrap", status=Status.ACTIVE)
        order2 = Order(item="Burger", status=Status.ACTIVE)

        self.active_list.add_order(order1)
        self.assertEqual(self.active_list.get_length(), 1)

        self.assertEqual(self.active_list.get_order_by_id(order1.order_id), order1)
        self.assertIsNone(self.active_list.get_order_by_id(order2.order_id))

    def test_edge_single_order_round_trip(self):
        order = Order(item="Soup", status=Status.ACTIVE)
        self.assertTrue(self.active_list.add_order(order))
        self.assertEqual(list(self.active_list), [order])
        self.assertEqual(self.active_list.remove_order(order), order)
        self.assertEqual(list(self.active_list), [])

    def test_edge_duplicate_add(self):
        order = Order(item="Soup", status=Status.ACTIVE)
        self.assertTrue(self.active_list.add_order(order))
        self.assertTrue(self.active_list.add_order(order))
        self.assertEqual(self.active_list.get_length(), 2)

    def test_edge_large_order_list(self):
        orders = [Order(item=f"item-{i}", status=Status.ACTIVE) for i in range(200)]
        for order in orders:
            self.assertTrue(self.active_list.add_order(order))

        self.assertEqual(self.active_list.get_length(), 200)
        self.assertEqual(self.active_list.get_order_by_id(orders[0].order_id), orders[0])
        self.assertEqual(self.active_list.get_order_by_id(orders[-1].order_id), orders[-1])

    def test_edge_empty_list_lookup_and_remove(self):
        missing = Order(item="Soup", status=Status.ACTIVE)
        self.assertEqual(self.active_list.get_length(), 0)
        self.assertIsNone(self.active_list.get_order_by_id(missing.order_id))
        self.assertIsNone(self.active_list.remove_order(missing))
        self.assertEqual(list(self.active_list), [])

    def test_invalid_add_none(self):
        with self.assertRaises(AttributeError):
            self.active_list.add_order(None)

    def test_invalid_lookup_wrong_id_type(self):
        order = Order(item="Soup", status=Status.ACTIVE)
        self.active_list.add_order(order)
        self.assertIsNone(self.active_list.get_order_by_id("not-a-uuid"))
        self.assertIsNone(self.active_list.get_order_by_id(None))
        self.assertEqual(self.active_list.get_order_by_id(uuid.uuid4()), None)


if __name__ == "__main__":
    unittest.main()