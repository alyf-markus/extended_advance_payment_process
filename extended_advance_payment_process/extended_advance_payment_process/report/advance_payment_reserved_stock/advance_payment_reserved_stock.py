# Copyright (c) 2026, Markus and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, flt, today

from extended_advance_payment_process.sales_order import is_paid

OPEN_RESERVATION_STATUSES = ["Partially Reserved", "Reserved", "Partially Delivered", "Partially Used"]


def execute(filters: dict | None = None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns() -> list[dict]:
	return [
		{
			"label": _("Sales Order"),
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"options": "Sales Order",
			"width": 150,
		},
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150,
		},
		{"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 150,
		},
		{"label": _("Reserved Qty"), "fieldname": "reserved_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Reserved Since"), "fieldname": "reserved_since", "fieldtype": "Datetime", "width": 160},
		{"label": _("Days Reserved"), "fieldname": "days_reserved", "fieldtype": "Int", "width": 110},
		{"label": _("Qty in Stock"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 110},
		{
			"label": _("Qty on Open Sales Orders"),
			"fieldname": "sales_order_qty",
			"fieldtype": "Float",
			"width": 160,
		},
		{
			"label": _("Payable Advance"),
			"fieldname": "payable_advance",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
		{
			"label": _("Advance Paid"),
			"fieldname": "advance_paid",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
		{"label": _("Paid"), "fieldname": "paid", "fieldtype": "Check", "width": 70},
		{
			"label": _("Stock Reservation Entry"),
			"fieldname": "stock_reservation_entry",
			"fieldtype": "Link",
			"options": "Stock Reservation Entry",
			"width": 160,
		},
		{
			"label": _("Currency"),
			"fieldname": "currency",
			"fieldtype": "Link",
			"options": "Currency",
			"hidden": 1,
		},
	]


def get_data(filters) -> list[dict]:
	order_filters = {"docstatus": 1, "custom_uses_advance_payment": 1}
	if filters.company:
		order_filters["company"] = filters.company
	if filters.sales_order:
		order_filters["name"] = filters.sales_order
	if filters.customer:
		order_filters["customer"] = filters.customer

	sales_orders = {
		order.name: order
		for order in frappe.get_all(
			"Sales Order",
			filters=order_filters,
			fields=["name", "customer", "currency", "custom_payable_advance", "advance_paid"],
		)
	}
	if not sales_orders:
		return []

	reservation_filters = {
		"docstatus": 1,
		"voucher_type": "Sales Order",
		"voucher_no": ["in", list(sales_orders)],
		"status": ["in", OPEN_RESERVATION_STATUSES],
	}
	if filters.item_code:
		reservation_filters["item_code"] = filters.item_code

	reservations = frappe.get_all(
		"Stock Reservation Entry",
		filters=reservation_filters,
		fields=["name", "voucher_no", "item_code", "warehouse", "reserved_qty", "delivered_qty", "creation"],
		order_by="creation asc",
	)
	if not reservations:
		return []

	bins = {
		(row.item_code, row.warehouse): row
		for row in frappe.get_all(
			"Bin",
			filters={
				"item_code": ["in", {row.item_code for row in reservations}],
				"warehouse": ["in", {row.warehouse for row in reservations}],
			},
			fields=["item_code", "warehouse", "actual_qty", "reserved_qty"],
		)
	}

	settings = frappe.get_single("Extended Advance Payment Process Settings")
	paid_by_order = {name: is_paid(frappe.get_doc("Sales Order", name), settings) for name in sales_orders}

	data = []
	for reservation in reservations:
		order = sales_orders[reservation.voucher_no]
		paid = paid_by_order[reservation.voucher_no]
		if filters.unpaid_only and paid:
			continue

		stock = bins.get((reservation.item_code, reservation.warehouse), frappe._dict())
		data.append(
			{
				"sales_order": order.name,
				"customer": order.customer,
				"item_code": reservation.item_code,
				"warehouse": reservation.warehouse,
				"reserved_qty": flt(reservation.reserved_qty) - flt(reservation.delivered_qty),
				"reserved_since": reservation.creation,
				"days_reserved": date_diff(today(), reservation.creation),
				"actual_qty": flt(stock.actual_qty),
				"sales_order_qty": flt(stock.reserved_qty),
				"payable_advance": order.custom_payable_advance,
				"advance_paid": order.advance_paid,
				"paid": 1 if paid else 0,
				"stock_reservation_entry": reservation.name,
				"currency": order.currency,
			}
		)

	return sorted(data, key=lambda row: row["days_reserved"], reverse=True)
