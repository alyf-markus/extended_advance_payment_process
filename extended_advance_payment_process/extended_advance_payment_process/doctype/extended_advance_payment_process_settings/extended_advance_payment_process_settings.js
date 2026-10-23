// Copyright (c) 2026, Markus and contributors
// For license information, please see license.txt

frappe.ui.form.on("Extended Advance Payment Process Settings", {
	refresh(frm) {
		frappe.call({
			method: "extended_advance_payment_process.extended_advance_payment_process.doctype.extended_advance_payment_process_settings.extended_advance_payment_process_settings.get_advance_templates",
			callback(r) {
				render_advance_templates(frm, r.message);
			},
		});
	},
});

function render_advance_templates(frm, templates) {
	const term_list_link = `<a href="/app/payment-term?custom_counts_for_advance=1">${__(
		"Payment Terms with 'Counts for Advance'"
	)}</a>`;

	if (!templates.length) {
		frm.fields_dict.advance_templates_html.$wrapper.html(
			`<p class="text-muted">${__(
				"No Payment Terms Template contains a Payment Term with 'Counts for Advance'."
			)}</p>
			<p>${term_list_link}</p>`
		);
		return;
	}

	const rows = templates
		.map(
			(row) => `<tr>
				<td><a href="/app/payment-terms-template/${encodeURIComponent(
					row.template
				)}">${frappe.utils.escape_html(row.template)}</a></td>
				<td>${row.terms.map((term) => frappe.utils.escape_html(term)).join(", ")}</td>
			</tr>`
		)
		.join("");

	frm.fields_dict.advance_templates_html.$wrapper.html(
		`<p class="text-muted">${__(
			"A Sales Order is blocked until the advance is paid if one of its payment terms has 'Counts for Advance' checked. These templates contain such a term:"
		)}</p>
		<table class="table table-bordered">
			<thead><tr><th>${__("Payment Terms Template")}</th><th>${__(
			"Advance Payment Terms"
		)}</th></tr></thead>
			<tbody>${rows}</tbody>
		</table>
		<p>${term_list_link}</p>`
	);
}
