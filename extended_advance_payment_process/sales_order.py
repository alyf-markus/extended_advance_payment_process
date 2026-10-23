import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime


def validate(doc, method=None):
	settings = frappe.get_single("Extended Advance Payment Process Settings")
	selected = [row.payment_term_templates for row in settings.templates_used]
	doc.custom_uses_advance_payment = 1 if doc.payment_terms_template in selected else 0
	if not doc.custom_uses_advance_payment:
		return
	doc.custom_payable_advance = get_advance_due(doc)
	set_reserve_stock(doc, settings)


def set_reserve_stock(doc, settings):
	if not frappe.db.get_single_value("Stock Settings", "enable_stock_reservation"):
		return
	doc.reserve_stock = 1 if settings.allow_reservation else 0


def get_advance_due(doc):
	due_now = sum(
		flt(row.payment_amount)
		for row in doc.payment_schedule
		if row.payment_term
		and frappe.db.get_value("Payment Term", row.payment_term, "custom_counts_for_advance")
	)
	return due_now or flt(doc.rounded_total) or flt(doc.grand_total)


def is_paid(doc, settings):
	if doc.party_account_currency != doc.currency:
		return False
	open_amount = get_advance_due(doc) - flt(doc.advance_paid)
	tolerance = flt(settings.payment_tolerance) if settings.allow_tolerance else 0
	return open_amount <= tolerance


@frappe.whitelist()
def set_release(name, side, release):
	if side not in ("order", "delivery"):
		frappe.throw(_("Unknown release"))

	settings = frappe.get_single("Extended Advance Payment Process Settings")
	if settings.allow_processing_role not in frappe.get_roles():
		frappe.throw(_("You are not allowed to release this order."))

	doc = frappe.get_doc("Sales Order", name)
	doc.check_permission("write")
	if doc.docstatus != 1 or not doc.custom_uses_advance_payment:
		return

	released = cint(release)
	prefix = "custom_order" if side == "order" else "custom_delivery"
	doc.db_set(
		{
			f"{prefix}_released": released,
			f"{prefix}_released_by": frappe.session.user if released else None,
			f"{prefix}_released_on": now_datetime() if released else None,
		},
		update_modified=True,
		notify=True,
	)

def require_release(sales_order_name, side):
	sales_order = frappe.get_doc("Sales Order", sales_order_name)
	if not sales_order.custom_uses_advance_payment:
		return

	settings = frappe.get_single("Extended Advance Payment Process Settings")
	if is_paid(sales_order, settings):
		return

	released = sales_order.custom_order_released if side == "order" else sales_order.custom_delivery_released
	if not released:
		frappe.throw(
			_("The advance payment was not received. No further processing is allowed. Sales Order {0}.").format(
				sales_order_name
			),
			title=_("Advance Payment"),
		)


def block_order(doc, method=None):
	for sales_order in {row.sales_order for row in doc.items if row.sales_order and not row.production_plan}:
		require_release(sales_order, "order")


def block_purchase_order(doc, method=None):
	for row in doc.items:
		if not row.sales_order:
			continue
		side = "delivery" if row.delivered_by_supplier else "order"
		require_release(row.sales_order, side)


def block_delivery(doc, method=None):
	for sales_order in {row.against_sales_order for row in doc.items if row.against_sales_order}:
		require_release(sales_order, "delivery")


def block_sales_invoice(doc, method=None):
	if not doc.update_stock:
		return
	for sales_order in {row.sales_order for row in doc.items if row.sales_order}:
		require_release(sales_order, "delivery")


def block_work_order(doc, method=None):
	if doc.sales_order:
		require_release(doc.sales_order, "order")


def block_subcontracting_order(doc, method=None):
	sales_orders = frappe.get_all(
		"Purchase Order Item",
		filters={"parent": doc.purchase_order, "sales_order": ["is", "set"]},
		pluck="sales_order",
		distinct=True,
	)
	for sales_order in sales_orders:
		require_release(sales_order, "order")


def block_subcontracting_inward_order(doc, method=None):
	require_release(doc.sales_order, "order")
