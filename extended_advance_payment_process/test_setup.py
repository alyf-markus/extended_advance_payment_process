import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field, delete_custom_fields
from frappe.tests import IntegrationTestCase

from extended_advance_payment_process.setup import get_custom_fields, make_custom_fields


def remove_other_app_field():
	delete_custom_fields({"Sales Order": [{"fieldname": "other_app_field"}]})
	frappe.db.commit()  # nosemgrep


class IntegrationTestSetup(IntegrationTestCase):
	def test_fields_of_other_apps_stay_untouched(self):
		# Creating a Custom Field commits, so the test rollback does not remove it.
		# A Column Break at least adds no database column.
		self.addCleanup(remove_other_app_field)
		create_custom_field(
			"Sales Order",
			{
				"fieldname": "other_app_field",
				"label": "Other App Field",
				"fieldtype": "Column Break",
				"insert_after": "advance_paid",
			},
		)
		other_field = frappe.get_doc("Custom Field", {"dt": "Sales Order", "fieldname": "other_app_field"})

		make_custom_fields()
		make_custom_fields()

		after = frappe.get_doc("Custom Field", other_field.name)
		self.assertEqual(after.label, "Other App Field")
		self.assertEqual(after.insert_after, "advance_paid")
		self.assertIsNone(after.module)
		self.assertEqual(after.modified, other_field.modified)

	def test_own_fields_are_created(self):
		make_custom_fields()
		for doctype, fields in get_custom_fields().items():
			for field in fields:
				self.assertTrue(
					frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}),
					f"{doctype}.{field['fieldname']} is missing",
				)

		no_copy = frappe.db.get_value(
			"Custom Field", {"dt": "Sales Order", "fieldname": "custom_order_released"}, "no_copy"
		)
		self.assertEqual(no_copy, 1)
