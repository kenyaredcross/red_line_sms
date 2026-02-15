// Copyright (c) 2025, Kelvin NJenga and contributors
// For license information, please see license.txt

frappe.ui.form.on("Send SMS", {
	refresh(frm) {
		setup_receiver_type_options(frm);
		setup_add_filter_button(frm);
		setup_character_counter(frm);
		update_contact_preview(frm);
	},

	receiver_type(frm) {
		if (frm.doc.receiver_type === "Manual Entry") {
			frm.set_value("contact_mapping", "");
			frm.doc.sms_filters = [];
			frm.refresh_field("sms_filters");
			clear_contact_preview(frm);
		} else if (frm.doc.receiver_type) {
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
						update_contact_preview(frm);
					}
				},
			});
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
			frm.set_df_property(
				"receiver_type",
				"options",
				options.join("\n")
			);
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
		return;
	}

	let btn = $(
		`<button class="btn btn-xs btn-default" style="margin-bottom: 10px;">+ Add Filter</button>`
	);

	btn.on("click", function () {
		show_filter_dialog(frm);
	});

	wrapper.append(btn);
}

function show_filter_dialog(frm) {
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "SMS Contact Mapping",
			name: frm.doc.contact_mapping,
		},
		callback(r) {
			if (!r.message) {
				frappe.msgprint(
					__("Please select a valid Recipient Source first.")
				);
				return;
			}
			fetch_and_show_fields(frm, r.message.source_doctype);
		},
	});
}

function fetch_and_show_fields(frm, source_doctype) {
	frappe.call({
		method: "red_line_sms.api.send_sms.get_filterable_fields",
		args: { doctype_name: source_doctype },
		callback(r) {
			if (!r.message || !r.message.length) {
				frappe.msgprint(
					__("No filterable fields found on {0}.", [source_doctype])
				);
				return;
			}
			let fields = r.message;

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
					row.filter_label = field_meta
						? field_meta.label
						: values.filter_field;
					row.filter_fieldtype = field_meta
						? field_meta.fieldtype
						: "Data";
					row.filter_doctype = field_meta
						? field_meta.options || ""
						: "";
					row.filter_value = values.filter_value;
					frm.refresh_field("sms_filters");
					d.hide();
					update_contact_preview(frm);
				},
			});

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

			let initial = d.get_value("filter_field");
			if (initial) {
				let field_meta = fields.find(
					(f) => f.fieldname === initial
				);
				update_value_field(d, field_meta);
			}
		},
	});
}

function update_value_field(dialog, field_meta) {
	if (!field_meta) return;

	let value_field = dialog.fields_dict.filter_value;

	if (field_meta.fieldtype === "Link" && field_meta.options) {
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
		value_field.df.fieldtype = "Link";
		value_field.df.options =
			field_meta.link_doctype || field_meta.options || "DocType";
		value_field.refresh();
	} else {
		value_field.df.fieldtype = "Data";
		value_field.df.options = "";
		value_field.refresh();
	}
}

// --- Character counter (uses the HTML field, no stacking toasts) ---

function setup_character_counter(frm) {
	let $input = frm.fields_dict.message?.$input;
	if (!$input) return;

	// Unbind previous handler to prevent stacking
	$input.off("input.sms_counter");

	$input.on("input.sms_counter", function () {
		render_character_count(frm, $(this).val().length);
	});

	// Render current count immediately
	render_character_count(frm, (frm.doc.message || "").length);
}

function render_character_count(frm, current_length) {
	let wrapper = frm.fields_dict.character_count?.$wrapper;
	if (!wrapper) return;

	let max_length = 160;
	let remaining = max_length - current_length;
	let color = remaining < 0 ? "red" : "var(--text-muted)";

	wrapper.html(
		`<div style="font-size: 12px; color: ${color}; padding: 4px 0;">
			Characters: ${current_length} / ${max_length} &mdash; Remaining: ${remaining >= 0 ? remaining : 0}
		</div>`
	);
}

// --- Contact count & cost preview ---

function update_contact_preview(frm) {
	let wrapper = frm.fields_dict.add_filter_html?.$wrapper;
	if (!wrapper) return;

	// Remove any existing preview
	wrapper.find(".sms-contact-preview").remove();

	if (
		!frm.doc.contact_mapping ||
		frm.doc.receiver_type === "Manual Entry"
	) {
		return;
	}

	let filters = (frm.doc.sms_filters || []).map((row) => ({
		filter_field: row.filter_field,
		filter_fieldtype: row.filter_fieldtype,
		filter_doctype: row.filter_doctype,
		filter_value: row.filter_value,
	}));

	frappe.call({
		method: "red_line_sms.api.send_sms.get_contact_count",
		args: {
			mapping_name: frm.doc.contact_mapping,
			filters: JSON.stringify(filters),
		},
		callback(r) {
			if (!r.message) return;

			let { count, estimated_cost } = r.message;
			let preview_html = `
				<div class="sms-contact-preview" style="
					padding: 8px 12px;
					margin-bottom: 10px;
					background: var(--bg-light-gray, #f5f7fa);
					border-radius: 6px;
					font-size: 13px;
				">
					<strong>${count}</strong> contact${count !== 1 ? "s" : ""} selected
					&mdash; Estimated cost: <strong>KES ${estimated_cost.toFixed(2)}</strong>
				</div>
			`;
			// Insert after the button (or at the end if no button)
			let existing = wrapper.find(".sms-contact-preview");
			if (existing.length) {
				existing.replaceWith(preview_html);
			} else {
				wrapper.append(preview_html);
			}
		},
	});
}

function clear_contact_preview(frm) {
	let wrapper = frm.fields_dict.add_filter_html?.$wrapper;
	if (wrapper) {
		wrapper.find(".sms-contact-preview").remove();
	}
}
