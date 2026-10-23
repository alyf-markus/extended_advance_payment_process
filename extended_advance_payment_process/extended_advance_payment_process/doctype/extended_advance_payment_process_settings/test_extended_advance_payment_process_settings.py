# Copyright (c) 2026, Markus and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = ["Payment Terms Template"]



class IntegrationTestExtendedAdvancePaymentProcessSettings(IntegrationTestCase):
	"""
	Integration tests for ExtendedAdvancePaymentProcessSettings.
	Use this class for testing interactions between multiple components.
	"""

	def test_template_without_advance_term_is_rejected(self):
		term = frappe.get_doc(
			{"doctype": "Payment Term", "payment_term_name": "EAPP Plain", "invoice_portion": 100}
		).insert()
		template = frappe.get_doc(
			{
				"doctype": "Payment Terms Template",
				"template_name": "EAPP Plain Template",
				"terms": [{"payment_term": term.name, "invoice_portion": 100, "credit_days": 0}],
			}
		).insert()

		settings = frappe.get_single("Extended Advance Payment Process Settings")
		settings.append("templates_used", {"payment_term_templates": template.name})
		with self.assertRaises(frappe.ValidationError):
			settings.validate()

		term.custom_counts_for_advance = 1
		term.save()
		settings.validate()
