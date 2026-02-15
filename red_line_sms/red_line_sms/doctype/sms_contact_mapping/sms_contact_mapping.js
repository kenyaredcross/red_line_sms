// Copyright (c) 2026, Kelvin NJenga and contributors
// For license information, please see license.txt

frappe.ui.form.on("SMS Contact Mapping", {
	source_doctype(frm) {
		// Clear dependent fields when source doctype changes
		frm.set_value("phone_field", "");
		frm.set_value("name_field", "");
		frm.set_value("active_filter_field", "");

		if (!frm.doc.source_doctype) return;

		// Fetch meta for the selected doctype and populate field options
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "DocField",
				filters: { parent: frm.doc.source_doctype },
				fields: ["fieldname", "label", "fieldtype"],
				limit_page_length: 0,
			},
			callback(r) {
				if (!r.message) return;
				let fields = r.message;

				let phone_options = fields
					.filter((f) =>
						["Data", "Phone", "Small Text"].includes(f.fieldtype)
					)
					.map((f) => f.fieldname);

				let name_options = fields
					.filter((f) => ["Data", "Link"].includes(f.fieldtype))
					.map((f) => f.fieldname);

				let active_options = fields
					.filter((f) =>
						["Check", "Select", "Data"].includes(f.fieldtype)
					)
					.map((f) => f.fieldname);

				frm.fields_dict.phone_field.df.options = phone_options.join(
					"\n"
				);
				frm.fields_dict.phone_field.df.fieldtype = "Autocomplete";
				frm.fields_dict.phone_field.refresh();

				frm.fields_dict.name_field.df.options = name_options.join("\n");
				frm.fields_dict.name_field.df.fieldtype = "Autocomplete";
				frm.fields_dict.name_field.refresh();

				frm.fields_dict.active_filter_field.df.options =
					active_options.join("\n");
				frm.fields_dict.active_filter_field.df.fieldtype =
					"Autocomplete";
				frm.fields_dict.active_filter_field.refresh();

				// Auto-set mapping_name from doctype if blank
				if (!frm.doc.mapping_name) {
					frm.set_value("mapping_name", frm.doc.source_doctype);
				}
			},
		});
	},
});
