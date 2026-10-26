from frappe.custom.doctype.custom_field.custom_field import create_custom_fields, delete_custom_fields

MODULE = "Extended Advance Payment Process"


def after_install():
	make_custom_fields()


def after_migrate():
	make_custom_fields()


def before_uninstall():
	delete_custom_fields(get_custom_fields())


def make_custom_fields():
	"""Create or update only the fields listed here. Fields of other apps stay untouched."""
	create_custom_fields(get_custom_fields())


def get_custom_fields():
	custom_fields = {
		"Payment Term": [
			{
				"fieldname": "custom_counts_for_advance",
				"label": "Counts for Advance",
				"fieldtype": "Check",
				"insert_after": "mode_of_payment",
				"in_list_view": 1,
			},
		],
		"Sales Order": [
			{
				"fieldname": "custom_column_break_awcqi",
				"fieldtype": "Column Break",
				"insert_after": "advance_paid",
			},
			{
				"fieldname": "custom_payable_advance",
				"label": "Payable Advance",
				"fieldtype": "Currency",
				"options": "party_account_currency",
				"insert_after": "custom_column_break_awcqi",
				"depends_on": "custom_uses_advance_payment",
				"read_only": 1,
			},
			{
				"fieldname": "custom_advance_payment_processing",
				"label": "Advance Payment Processing",
				"fieldtype": "Section Break",
				"insert_after": "custom_payable_advance",
				"depends_on": "custom_uses_advance_payment",
			},
			{
				"fieldname": "custom_column_break_8pdis",
				"fieldtype": "Column Break",
				"insert_after": "custom_advance_payment_processing",
			},
			*release_fields("delivery", "Delivery", insert_after="custom_column_break_8pdis"),
			{
				"fieldname": "custom_column_break_fl1pq",
				"fieldtype": "Column Break",
				"insert_after": "custom_delivery_released_on",
			},
			*release_fields("order", "Order", insert_after="custom_column_break_fl1pq"),
			{
				"fieldname": "custom_column_break_fcan2",
				"fieldtype": "Column Break",
				"insert_after": "custom_order_released_on",
				"hidden": 1,
				"read_only": 1,
				"allow_on_submit": 1,
			},
			{
				"fieldname": "custom_uses_advance_payment",
				"label": "uses_advance_payment",
				"fieldtype": "Check",
				"insert_after": "custom_column_break_fcan2",
				"hidden": 1,
				"read_only": 1,
				"allow_on_submit": 1,
			},
		],
	}

	for fields in custom_fields.values():
		for field in fields:
			field["module"] = MODULE

	return custom_fields


def release_fields(side, label, insert_after):
	"""Flag, user and time of one release side. Not copied, so a duplicated order starts unreleased."""
	common = {"read_only": 1, "allow_on_submit": 1, "no_copy": 1}
	return [
		{
			"fieldname": f"custom_{side}_released",
			"label": f"{label} Released",
			"fieldtype": "Check",
			"insert_after": insert_after,
			**common,
		},
		{
			"fieldname": f"custom_{side}_released_by",
			"label": f"{label} Released By",
			"fieldtype": "Link",
			"options": "User",
			"insert_after": f"custom_{side}_released",
			**common,
		},
		{
			"fieldname": f"custom_{side}_released_on",
			"label": f"{label} Released On",
			"fieldtype": "Datetime",
			"insert_after": f"custom_{side}_released_by",
			**common,
		},
	]
