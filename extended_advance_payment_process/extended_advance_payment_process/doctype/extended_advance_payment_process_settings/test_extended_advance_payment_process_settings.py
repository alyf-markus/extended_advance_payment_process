# Copyright (c) 2026, Markus and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from extended_advance_payment_process.extended_advance_payment_process.doctype.extended_advance_payment_process_settings.extended_advance_payment_process_settings import (
	get_advance_templates,
)

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestExtendedAdvancePaymentProcessSettings(IntegrationTestCase):
	"""
	Integration tests for ExtendedAdvancePaymentProcessSettings.
	Use this class for testing interactions between multiple components.
	"""

	def test_lists_only_templates_with_advance_term(self):
		advance = frappe.get_doc(
			{
				"doctype": "Payment Term",
				"payment_term_name": "EAPP Deposit",
				"invoice_portion": 30,
				"custom_counts_for_advance": 1,
			}
		).insert()
		rest = frappe.get_doc(
			{"doctype": "Payment Term", "payment_term_name": "EAPP Balance", "invoice_portion": 70}
		).insert()
		frappe.get_doc(
			{
				"doctype": "Payment Terms Template",
				"template_name": "EAPP With Deposit",
				"terms": [
					{"payment_term": advance.name, "invoice_portion": 30, "credit_days": 0},
					{"payment_term": rest.name, "invoice_portion": 70, "credit_days": 30},
				],
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "Payment Terms Template",
				"template_name": "EAPP Without Deposit",
				"terms": [{"payment_term": rest.name, "invoice_portion": 100, "credit_days": 30}],
			}
		).insert()

		templates = {row["template"]: row["terms"] for row in get_advance_templates()}
		self.assertEqual(templates["EAPP With Deposit"], ["EAPP Deposit"])
		self.assertNotIn("EAPP Without Deposit", templates)
