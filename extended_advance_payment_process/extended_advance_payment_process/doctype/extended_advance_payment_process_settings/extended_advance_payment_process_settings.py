# Copyright (c) 2026, Markus and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ExtendedAdvancePaymentProcessSettings(Document):
	def validate(self):
		for row in self.templates_used:
			template = row.payment_term_templates
			term_names = [term.payment_term for term in frappe.get_doc("Payment Terms Template", template).terms]
			advance_terms = frappe.get_all(
				"Payment Term",
				filters={"name": ["in", term_names], "custom_counts_for_advance": 1},
				pluck="name",
			)
			if not advance_terms:
				frappe.throw(
					_("Row {0}: Payment Terms Template {1} has no Payment Term with 'Counts for Advance'.").format(
						row.idx, template
					)
				)
