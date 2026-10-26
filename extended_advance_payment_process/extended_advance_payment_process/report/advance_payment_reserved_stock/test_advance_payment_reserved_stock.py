import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from extended_advance_payment_process.extended_advance_payment_process.report.advance_payment_reserved_stock.advance_payment_reserved_stock import (
	execute,
)


class IntegrationTestAdvancePaymentReservedStock(IntegrationTestCase):
	"""Records are written with db_insert, so ERPNext test fixtures are not needed."""

	def setUp(self):
		if not frappe.db.exists("Payment Term", "EAPP Report Advance"):
			frappe.get_doc(
				{
					"doctype": "Payment Term",
					"payment_term_name": "EAPP Report Advance",
					"invoice_portion": 100,
					"custom_counts_for_advance": 1,
				}
			).insert()

	def make_order(self, name, advance_paid):
		order = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"name": name,
				"docstatus": 1,
				"customer": "EAPP Customer",
				"company": "EAPP Company",
				"currency": "EUR",
				"party_account_currency": "EUR",
				"grand_total": 100,
				"rounded_total": 100,
				"advance_paid": advance_paid,
				"custom_uses_advance_payment": 1,
				"custom_payable_advance": 100,
				"payment_schedule": [{"payment_term": "EAPP Report Advance", "payment_amount": 100}],
			}
		)
		order.db_insert()
		for row in order.payment_schedule:
			row.db_insert()

	def make_reservation(self, sales_order, days_ago):
		reservation = frappe.get_doc(
			{
				"doctype": "Stock Reservation Entry",
				"name": f"EAPP-SRE-{sales_order}",
				"docstatus": 1,
				"status": "Reserved",
				"voucher_type": "Sales Order",
				"voucher_no": sales_order,
				"item_code": "EAPP Item",
				"warehouse": "EAPP Warehouse",
				"company": "EAPP Company",
				"reserved_qty": 5,
				"delivered_qty": 2,
			}
		)
		reservation.db_insert()
		frappe.db.set_value(
			"Stock Reservation Entry",
			reservation.name,
			"creation",
			add_days(now_datetime(), -days_ago),
			update_modified=False,
		)

	def test_lists_reserved_stock_of_advance_orders(self):
		self.make_order("EAPP-SO-UNPAID", advance_paid=0)
		self.make_order("EAPP-SO-PAID", advance_paid=100)
		self.make_reservation("EAPP-SO-UNPAID", days_ago=10)
		self.make_reservation("EAPP-SO-PAID", days_ago=3)
		frappe.get_doc(
			{
				"doctype": "Bin",
				"name": "EAPP-BIN",
				"item_code": "EAPP Item",
				"warehouse": "EAPP Warehouse",
				"actual_qty": 12,
				"reserved_qty": 8,
			}
		).db_insert()

		_columns, data = execute({"company": "EAPP Company", "unpaid_only": 1})
		self.assertEqual([row["sales_order"] for row in data], ["EAPP-SO-UNPAID"])
		row = data[0]
		self.assertEqual(row["reserved_qty"], 3)
		self.assertEqual(row["days_reserved"], 10)
		self.assertEqual(row["actual_qty"], 12)
		self.assertEqual(row["sales_order_qty"], 8)
		self.assertEqual(row["paid"], 0)

		_columns, data = execute({"company": "EAPP Company", "unpaid_only": 0})
		self.assertEqual([row["sales_order"] for row in data], ["EAPP-SO-UNPAID", "EAPP-SO-PAID"])
