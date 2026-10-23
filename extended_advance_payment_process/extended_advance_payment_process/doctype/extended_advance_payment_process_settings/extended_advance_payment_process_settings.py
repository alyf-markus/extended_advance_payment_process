# Copyright (c) 2026, Markus and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ExtendedAdvancePaymentProcessSettings(Document):
	pass


@frappe.whitelist()
def get_advance_templates():
	"""Payment Terms Templates that contain at least one Payment Term with 'Counts for Advance'."""
	advance_terms = frappe.get_all("Payment Term", filters={"custom_counts_for_advance": 1}, pluck="name")
	if not advance_terms:
		return []

	rows = frappe.get_all(
		"Payment Terms Template Detail",
		filters={"parenttype": "Payment Terms Template", "payment_term": ["in", advance_terms]},
		fields=["parent", "payment_term"],
		order_by="parent, idx",
	)
	templates = {}
	for row in rows:
		templates.setdefault(row.parent, []).append(row.payment_term)
	return [{"template": template, "terms": terms} for template, terms in templates.items()]
