import unittest
from datetime import datetime, timedelta
from order import Order, OrderList, Status


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



if __name__ == "__main__":
    unittest.main()