from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from extended_advance_payment_process.sales_order import (
	block_delivery,
	block_purchase_order,
	block_subcontracting_inward_order,
	block_subcontracting_order,
	get_advance_due,
	is_paid,
	set_release,
	validate,
)


def make_payment_terms():
	if not frappe.db.exists("Payment Term", "EAPP Advance"):
		frappe.get_doc(
			{
				"doctype": "Payment Term",
				"payment_term_name": "EAPP Advance",
				"invoice_portion": 30,
				"custom_counts_for_advance": 1,
			}
		).insert()
	if not frappe.db.exists("Payment Term", "EAPP Rest"):
		frappe.get_doc(
			{"doctype": "Payment Term", "payment_term_name": "EAPP Rest", "invoice_portion": 70}
		).insert()


class IntegrationTestIsPaid(IntegrationTestCase):
	def setUp(self):
		make_payment_terms()
		self.settings = frappe._dict(allow_tolerance=1, payment_tolerance=0.02)

	def order(self, advance_paid, **kwargs):
		values = {
			"party_account_currency": "EUR",
			"currency": "EUR",
			"rounded_total": 100,
			"grand_total": 100,
			"advance_paid": advance_paid,
			"payment_schedule": [
				frappe._dict(payment_term="EAPP Advance", payment_amount=30),
				frappe._dict(payment_term="EAPP Rest", payment_amount=70),
			],
		}
		values.update(kwargs)
		return frappe._dict(values)

	def test_only_flagged_rows_count(self):
		self.assertTrue(is_paid(self.order(30), self.settings))
		self.assertFalse(is_paid(self.order(29), self.settings))

	def test_payable_advance_is_sum_of_flagged_rows(self):
		self.assertEqual(get_advance_due(self.order(0)), 30)

	def test_tolerance(self):
		self.assertTrue(is_paid(self.order(29.98), self.settings))
		self.settings.allow_tolerance = 0
		self.assertFalse(is_paid(self.order(29.98), self.settings))

	def test_flagged_row_marks_order_as_advance_payment(self):
		order = self.order(0)
		validate(order)
		self.assertEqual(order.custom_payable_advance, 30)
		self.assertEqual(order.custom_uses_advance_payment, 1)

	def test_no_flagged_row_is_no_advance_payment(self):
		order = self.order(0, payment_schedule=[frappe._dict(payment_term="EAPP Rest", payment_amount=100)])
		validate(order)
		self.assertEqual(order.custom_payable_advance, 0)
		self.assertEqual(order.custom_uses_advance_payment, 0)

	def test_currency_mismatch_is_not_paid(self):
		self.assertFalse(is_paid(self.order(100, party_account_currency="USD"), self.settings))


class IntegrationTestBlockers(IntegrationTestCase):
	"""The Sales Order is replaced at the frappe.get_doc boundary."""

	def setUp(self):
		make_payment_terms()

	def sales_order(self, paid=False, order_released=0, delivery_released=0):
		return frappe._dict(
			custom_uses_advance_payment=1,
			custom_order_released=order_released,
			custom_delivery_released=delivery_released,
			payment_schedule=[
				frappe._dict(payment_term="EAPP Advance", payment_amount=30),
				frappe._dict(payment_term="EAPP Rest", payment_amount=70),
			],
			party_account_currency="EUR",
			currency="EUR",
			rounded_total=100,
			grand_total=100,
			advance_paid=30 if paid else 0,
		)

	def run_with(self, sales_order, function, doc):
		real_get_doc = frappe.get_doc

		def fake_get_doc(doctype, *args, **kwargs):
			if doctype == "Sales Order":
				return sales_order
			return real_get_doc(doctype, *args, **kwargs)

		with patch.object(frappe, "get_doc", fake_get_doc):
			function(doc)

	def test_unpaid_order_blocks_purchase_order(self):
		doc = SimpleNamespace(items=[frappe._dict(sales_order="SO-1", delivered_by_supplier=0)])
		with self.assertRaises(frappe.ValidationError):
			self.run_with(self.sales_order(), block_purchase_order, doc)

	def test_order_release_unblocks_order_but_not_delivery(self):
		order = self.sales_order(order_released=1)
		order_doc = SimpleNamespace(items=[frappe._dict(sales_order="SO-1", delivered_by_supplier=0)])
		self.run_with(order, block_purchase_order, order_doc)

		drop_ship = SimpleNamespace(items=[frappe._dict(sales_order="SO-1", delivered_by_supplier=1)])
		with self.assertRaises(frappe.ValidationError):
			self.run_with(order, block_purchase_order, drop_ship)

	def test_paid_order_is_not_blocked(self):
		doc = SimpleNamespace(items=[frappe._dict(against_sales_order="SO-1")])
		self.run_with(self.sales_order(paid=True), block_delivery, doc)

	def test_unpaid_order_blocks_delivery_note(self):
		doc = SimpleNamespace(items=[frappe._dict(against_sales_order="SO-1")])
		with self.assertRaises(frappe.ValidationError):
			self.run_with(self.sales_order(), block_delivery, doc)

	def test_subcontracting_order_is_blocked_via_purchase_order_item(self):
		doc = frappe._dict(purchase_order="PO-1")
		with patch.object(frappe, "get_all", return_value=["SO-1"]):
			with self.assertRaises(frappe.ValidationError):
				self.run_with(self.sales_order(), block_subcontracting_order, doc)
			self.run_with(self.sales_order(order_released=1), block_subcontracting_order, doc)

	def test_subcontracting_inward_order_is_blocked(self):
		doc = frappe._dict(sales_order="SO-1")
		with self.assertRaises(frappe.ValidationError):
			self.run_with(self.sales_order(), block_subcontracting_inward_order, doc)

	def test_release_needs_the_processing_role(self):
		with patch.object(frappe, "get_roles", return_value=["Guest"]):
			with self.assertRaises(frappe.ValidationError):
				set_release("SO-1", "order", 1)
