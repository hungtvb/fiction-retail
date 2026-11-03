"""Integration checks for the standalone November 2026 release."""
import unittest

from scripts import build_unified


class UnifiedReleaseTests(unittest.TestCase):
    def test_load_order_puts_parents_before_large_child_tables(self):
        order = build_unified.LOAD_ORDER
        self.assertLess(order.index('orders'), order.index('order_items'))
        self.assertLess(order.index('products'), order.index('order_items'))
        self.assertLess(order.index('fulfillment_cases'),
                        order.index('inventory_snapshots_v2'))

    def test_date_shift_preserves_timestamp_suffix(self):
        self.assertEqual('2026-10-27T10:05:00.000Z',
                         build_unified.shift_date('2024-04-24T10:05:00.000Z', 916))
        self.assertEqual('2026-11-02', build_unified.shift_date('2024-04-30', 916))

    def test_sku_is_stable_across_ordering(self):
        product_ids = ['b', 'a', 'c']
        first = {pid: build_unified.sku_for(pid) for pid in product_ids}
        second = {pid: build_unified.sku_for(pid) for pid in reversed(product_ids)}
        self.assertEqual(first, second)
        self.assertEqual(3, len(set(first.values())))

if __name__ == '__main__':
    unittest.main()
