frappe.ui.form.on("Sales Order", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1 || !frm.doc.custom_uses_advance_payment) {
			return;
		}

		add_release_button(frm, "order", "Order");
		add_release_button(frm, "delivery", "Delivery");
	},
});

function add_release_button(frm, side, label) {
	const released = frm.doc[`custom_${side}_released`];
	const button_label = released ? __(`Revoke ${label} Release`) : __(`Release ${label}`);

	frm.add_custom_button(
		button_label,
		() => {
			frappe.call({
				method: "extended_advance_payment_process.sales_order.set_release",
				args: {
					name: frm.doc.name,
					side,
					release: released ? 0 : 1,
				},
				callback() {
					frm.reload_doc();
				},
			});
		},
		__("Advance Payment")
	);
}
