// Copyright (c) 2025, Kelvin NJenga and contributors
// For license information, please see license.txt

frappe.ui.form.on("Send SMS", {
	refresh(frm) {
        check_sms_length(frm);
	},
    validate: function (frm) {
        check_sms_length(frm);
        
    },
    message: function(frm) {
        check_sms_length(frm);
    }
});

function check_sms_length (frm) {
    if (frm.doc.message && frm.doc.message.length > 160){
            ftappe.throw(__("The SMS cannot exceed 160 characters"));
        };
};


