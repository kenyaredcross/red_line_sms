// Copyright (c) 2025, Kelvin NJenga and contributors
// For license information, please see license.txt

frappe.ui.form.on("Send SMS", {
	refresh(frm) {
		setup_receiver_type_options(frm);
		setup_add_filter_button(frm);
		check_sms_length(frm);
	},

	receiver_type(frm) {
		if (frm.doc.receiver_type === "Manual Entry") {
			frm.set_value("contact_mapping", "");
			frm.doc.sms_filters = [];
			frm.refresh_field("sms_filters");
		} else if (frm.doc.receiver_type) {
			// Look up the mapping by name
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "SMS Contact Mapping",
					filters: { mapping_name: frm.doc.receiver_type },
					fields: ["name"],
					limit_page_length: 1,
				},
				callback(r) {
					if (r.message && r.message.length) {
						frm.set_value("contact_mapping", r.message[0].name);
					}
				},
			});
			// Clear old filters when mapping changes
			frm.doc.sms_filters = [];
			frm.refresh_field("sms_filters");
		}
		setup_add_filter_button(frm);
	},
});

function setup_receiver_type_options(frm) {
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "SMS Contact Mapping",
			fields: ["mapping_name"],
			limit_page_length: 0,
			order_by: "mapping_name asc",
		},
		callback(r) {
			let options = ["Manual Entry"];
			if (r.message) {
				r.message.forEach((m) => {
					options.push(m.mapping_name);
				});
			}
			frm.set_df_property("receiver_type", "options", options.join("\n"));
			frm.refresh_field("receiver_type");
		},
	});
}

function setup_add_filter_button(frm) {
	let wrapper = frm.fields_dict.add_filter_html?.$wrapper;
	if (!wrapper) return;

	wrapper.empty();

	if (!frm.doc.receiver_type || frm.doc.receiver_type === "Manual Entry") {
		return;
	}

	if (frm.doc.docstatus === 1) {
		// Don't show button on submitted docs
		return;
	}

	let btn = $(`<button class="btn btn-xs btn-default" style="margin-bottom: 10px;">
		+ Add Filter
	</button>`);

	btn.on("click", function () {
		show_filter_dialog(frm);
	});

	wrapper.append(btn);
}

function show_filter_dialog(frm) {
	// First get the mapping to find source doctype
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "SMS Contact Mapping",
			name: frm.doc.contact_mapping,
		},
		callback(r) {
			if (!r.message) {
				frappe.msgprint(__("Please select a valid Recipient Source first."));
				return;
			}
			let mapping = r.message;
			fetch_and_show_fields(frm, mapping.source_doctype);
		},
	});
}

function fetch_and_show_fields(frm, source_doctype) {
	frappe.call({
		method: "red_line_sms.api.send_sms.get_filterable_fields",
		args: { doctype_name: source_doctype },
		callback(r) {
			if (!r.message || !r.message.length) {
				frappe.msgprint(__("No filterable fields found on {0}.", [source_doctype]));
				return;
			}
			let fields = r.message;

			// Build field selection options
			let field_options = fields.map((f) => ({
				label: `${f.label} (${f.fieldtype})`,
				value: f.fieldname,
			}));

			let d = new frappe.ui.Dialog({
				title: __("Add Filter"),
				fields: [
					{
						fieldname: "filter_field",
						fieldtype: "Select",
						label: __("Field"),
						options: field_options.map((o) => o.value),
						reqd: 1,
						change() {
							let selected = d.get_value("filter_field");
							let field_meta = fields.find(
								(f) => f.fieldname === selected
							);
							update_value_field(d, field_meta);
						},
					},
					{
						fieldname: "filter_value",
						fieldtype: "Data",
						label: __("Value"),
						reqd: 1,
					},
				],
				primary_action_label: __("Add"),
				primary_action(values) {
					let field_meta = fields.find(
						(f) => f.fieldname === values.filter_field
					);
					let row = frm.add_child("sms_filters");
					row.filter_field = values.filter_field;
					row.filter_label = field_meta ? field_meta.label : values.filter_field;
					row.filter_fieldtype = field_meta ? field_meta.fieldtype : "Data";
					row.filter_doctype = field_meta ? field_meta.options || "" : "";
					row.filter_value = values.filter_value;
					frm.refresh_field("sms_filters");
					d.hide();
				},
			});

			// Set display labels for the select
			let select_field = d.fields_dict.filter_field;
			if (select_field && select_field.$input) {
				select_field.$input.empty();
				field_options.forEach((o) => {
					select_field.$input.append(
						`<option value="${o.value}">${o.label}</option>`
					);
				});
			}

			d.show();

			// Trigger initial update for value field
			let initial = d.get_value("filter_field");
			if (initial) {
				let field_meta = fields.find((f) => f.fieldname === initial);
				update_value_field(d, field_meta);
			}
		},
	});
}

function update_value_field(dialog, field_meta) {
	if (!field_meta) return;

	let value_field = dialog.fields_dict.filter_value;

	if (field_meta.fieldtype === "Link" && field_meta.options) {
		// Replace with a Link field
		value_field.df.fieldtype = "Link";
		value_field.df.options = field_meta.options;
		value_field.refresh();
	} else if (field_meta.fieldtype === "Select" && field_meta.options) {
		value_field.df.fieldtype = "Select";
		value_field.df.options = field_meta.options;
		value_field.refresh();
	} else if (field_meta.fieldtype === "Check") {
		value_field.df.fieldtype = "Select";
		value_field.df.options = "0\n1";
		value_field.refresh();
	} else if (field_meta.fieldtype === "Table MultiSelect") {
		// For Table MultiSelect, link to the actual linked doctype (not the child table)
		value_field.df.fieldtype = "Link";
		value_field.df.options = field_meta.link_doctype || field_meta.options || "DocType";
		value_field.refresh();
	} else {
		value_field.df.fieldtype = "Data";
		value_field.df.options = "";
		value_field.refresh();
	}
}

function check_sms_length(frm) {
	if (frm.doc.message && frm.doc.message.length > 160) {
		frappe.throw(
			__(
				`The SMS cannot exceed 160 characters, your current count is ${frm.doc.message.length}`
			)
		);
	}

	if (frm.fields_dict.message && frm.fields_dict.message.$input) {
		frm.fields_dict.message.$input.on("input", function () {
			let current_length = $(this).val().length;
			let max_length = 160;
			let remaining = max_length - current_length;

			frm.set_intro(
				`characters used: ${current_length}/ ${max_length}. Remaining: ${remaining >= 0 ? remaining : 0}`,
				remaining < 0 ? "red" : "blue"
			);
		});
	}
}
